"""
Fusion 360 Natural-Language CAD Co-Pilot - Action Log

This module provides comprehensive action logging, persistence, and export
functionality for audit trails and operation replay.

Author: Fusion CoPilot Team
License: MIT
"""

import json
import csv
import os
import hashlib
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ActionLogEntry:
    """
    Represents a single action log entry with complete audit information.
    """
    
    def __init__(self, plan_id: str, plan_data: Dict, execution_result: Dict,
                 timeline_mapping: Optional[Dict] = None):
        """
        Initialize an action log entry.
        
        Args:
            plan_id: Unique identifier for the executed plan
            plan_data: Complete plan data that was executed
            execution_result: Results of plan execution
            timeline_mapping: Mapping of operations to Fusion timeline nodes
        """
        self.entry_id = self._generate_entry_id()
        self.timestamp = datetime.utcnow()
        self.plan_id = plan_id
        self.plan_data = plan_data
        self.execution_result = execution_result
        self.timeline_mapping = timeline_mapping or {}
        self.checksum = self._calculate_checksum()
        
        # Extract key metadata
        self.natural_language_prompt = plan_data.get('metadata', {}).get(
            'natural_language_prompt', 'Unknown prompt'
        )
        self.operation_count = len(plan_data.get('operations', []))
        self.execution_duration = execution_result.get('duration_seconds', 0)
        self.success = execution_result.get('success', False)
        self.error_message = execution_result.get('error_message')
    
    def _generate_entry_id(self) -> str:
        """Generate unique entry ID."""
        timestamp_str = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        random_suffix = hashlib.md5(str(datetime.utcnow()).encode()).hexdigest()[:8]
        return f"entry_{timestamp_str}_{random_suffix}"
    
    def _calculate_checksum(self) -> str:
        """Calculate CRC checksum for data integrity."""
        data_str = json.dumps({
            'plan_id': self.plan_id,
            'plan_data': self.plan_data,
            'execution_result': self.execution_result,
            'timeline_mapping': self.timeline_mapping
        }, sort_keys=True)
        
        return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict:
        """Convert entry to dictionary for serialization."""
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat() + 'Z',
            'plan_id': self.plan_id,
            'natural_language_prompt': self.natural_language_prompt,
            'operation_count': self.operation_count,
            'execution_duration': self.execution_duration,
            'success': self.success,
            'error_message': self.error_message,
            'plan_data': self.plan_data,
            'execution_result': self.execution_result,
            'timeline_mapping': self.timeline_mapping,
            'checksum': self.checksum
        }
    
    def get_human_readable_summary(self) -> str:
        """Generate human-readable summary of the action."""
        operations = self.plan_data.get('operations', [])
        
        if not operations:
            return f"Empty plan: {self.natural_language_prompt}"
        
        # Create concise operation summary
        op_summary = []
        for op in operations[:5]:  # Show first 5 operations
            op_type = op.get('op', 'unknown')
            params = op.get('params', {})
            
            if op_type == 'create_sketch':
                op_summary.append(f"sketch({params.get('name', 'unnamed')})")
            elif op_type == 'draw_rectangle':
                width = self._extract_param_value(params.get('width'))
                height = self._extract_param_value(params.get('height'))
                op_summary.append(f"rectangle({width}x{height})")
            elif op_type == 'draw_circle':
                diameter = self._extract_param_value(params.get('diameter'))
                op_summary.append(f"circle(⌀{diameter})")
            elif op_type == 'extrude':
                distance = self._extract_param_value(params.get('distance'))
                op_summary.append(f"extrude({distance})")
            elif op_type == 'create_hole':
                diameter = self._extract_param_value(params.get('diameter'))
                op_summary.append(f"hole(⌀{diameter})")
            elif op_type == 'fillet':
                radius = self._extract_param_value(params.get('radius'))
                op_summary.append(f"fillet(R{radius})")
            else:
                op_summary.append(op_type)
        
        if len(operations) > 5:
            op_summary.append(f"...+{len(operations) - 5} more")
        
        status = "✓" if self.success else "✗"
        return f"{status} {' → '.join(op_summary)}"
    
    def _extract_param_value(self, param: Any) -> str:
        """Extract displayable value from parameter."""
        if isinstance(param, dict):
            if 'value' in param and 'unit' in param:
                return f"{param['value']}{param['unit']}"
            elif 'value' in param:
                return str(param['value'])
        elif isinstance(param, (int, float)):
            return str(param)
        return str(param) if param is not None else "?"


class ActionLogger:
    """
    Comprehensive action logging system with persistence and export capabilities.
    """
    
    def __init__(self, log_directory: Optional[str] = None, settings: Optional[Dict] = None):
        """
        Initialize the action logger.
        
        Args:
            log_directory: Directory for log files (default: logs/actions)
            settings: Configuration settings
        """
        self.settings = settings or {}
        self.log_directory = Path(log_directory or "logs/actions")
        self.log_directory.mkdir(parents=True, exist_ok=True)
        
        self.session_entries: List[ActionLogEntry] = []
        self.current_session_file = self._get_session_filename()
        
        # Configuration
        self.auto_save = self.settings.get('auto_save_logs', True)
        self.max_log_age_days = self.settings.get('max_log_age_days', 90)
        self.compress_old_logs = self.settings.get('compress_old_logs', True)
        
        logger.info(f"Action logger initialized with directory: {self.log_directory}")
    
    def log_action(self, plan_id: str, plan_data: Dict, execution_result: Dict,
                   timeline_mapping: Optional[Dict] = None) -> str:
        """
        Log a completed action.
        
        Args:
            plan_id: Unique identifier for the executed plan
            plan_data: Complete plan data that was executed
            execution_result: Results of plan execution
            timeline_mapping: Mapping of operations to Fusion timeline nodes
            
        Returns:
            Entry ID of the logged action
        """
        entry = ActionLogEntry(plan_id, plan_data, execution_result, timeline_mapping)
        self.session_entries.append(entry)
        
        logger.info(f"Logged action: {entry.entry_id} for plan: {plan_id}")
        
        if self.auto_save:
            self._save_session_log()
        
        return entry.entry_id
    
    def get_session_log(self) -> List[ActionLogEntry]:
        """Get all entries from current session."""
        return self.session_entries.copy()
    
    def get_recent_entries(self, count: int = 10) -> List[ActionLogEntry]:
        """Get most recent entries across all logs."""
        all_entries = []
        
        # Add current session entries
        all_entries.extend(self.session_entries)
        
        # Load recent log files
        log_files = sorted(self.log_directory.glob("action_log_*.json"), reverse=True)
        
        for log_file in log_files[:5]:  # Check last 5 log files
            try:
                entries = self._load_log_file(log_file)
                all_entries.extend(entries)
            except Exception as e:
                logger.warning(f"Failed to load log file {log_file}: {e}")
        
        # Sort by timestamp and return most recent
        all_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return all_entries[:count]
    
    def export_action_log(self, format: str = 'json', filename: Optional[str] = None,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> str:
        """
        Export action log in specified format.
        
        Args:
            format: Export format ('json', 'csv', 'txt')
            filename: Output filename (auto-generated if None)
            start_date: Filter entries after this date
            end_date: Filter entries before this date
            
        Returns:
            Path to exported file
        """
        # Collect entries to export
        entries_to_export = self._collect_entries_for_export(start_date, end_date)
        
        if not entries_to_export:
            raise ValueError("No entries found for export criteria")
        
        # Generate filename if not provided
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"action_log_export_{timestamp}.{format}"
        
        export_path = self.log_directory / filename
        
        # Export in requested format
        if format == 'json':
            self._export_json(entries_to_export, export_path)
        elif format == 'csv':
            self._export_csv(entries_to_export, export_path)
        elif format == 'txt':
            self._export_txt(entries_to_export, export_path)
        else:
            raise ValueError(f"Unsupported export format: {format}")
        
        logger.info(f"Exported {len(entries_to_export)} entries to {export_path}")
        return str(export_path)
    
    def replay_action(self, entry_id: str) -> Dict:
        """
        Prepare action for replay by retrieving its plan data.
        
        Args:
            entry_id: ID of the action to replay
            
        Returns:
            Dictionary with plan data and metadata for replay
        """
        # Search in current session first
        for entry in self.session_entries:
            if entry.entry_id == entry_id:
                return self._prepare_replay_data(entry)
        
        # Search in historical logs
        log_files = sorted(self.log_directory.glob("action_log_*.json"), reverse=True)
        
        for log_file in log_files:
            try:
                entries = self._load_log_file(log_file)
                for entry in entries:
                    if entry.entry_id == entry_id:
                        return self._prepare_replay_data(entry)
            except Exception as e:
                logger.warning(f"Failed to search log file {log_file}: {e}")
        
        raise ValueError(f"Action entry not found: {entry_id}")
    
    def get_statistics(self) -> Dict:
        """Get usage statistics from action logs."""
        all_entries = self.get_recent_entries(1000)  # Last 1000 entries
        
        if not all_entries:
            return {
                'total_actions': 0,
                'success_rate': 0.0,
                'avg_duration': 0.0,
                'most_common_operations': [],
                'recent_activity': []
            }
        
        # Calculate statistics
        total_actions = len(all_entries)
        successful_actions = sum(1 for entry in all_entries if entry.success)
        success_rate = successful_actions / total_actions if total_actions > 0 else 0
        
        durations = [entry.execution_duration for entry in all_entries if entry.execution_duration > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        # Count operation types
        operation_counts = {}
        for entry in all_entries:
            for op in entry.plan_data.get('operations', []):
                op_type = op.get('op', 'unknown')
                operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
        
        most_common_ops = sorted(operation_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_entries = [e for e in all_entries if e.timestamp >= week_ago]
        
        return {
            'total_actions': total_actions,
            'success_rate': round(success_rate * 100, 1),
            'avg_duration': round(avg_duration, 2),
            'most_common_operations': most_common_ops,
            'recent_activity': len(recent_entries),
            'oldest_entry': min(all_entries, key=lambda x: x.timestamp).timestamp.isoformat() if all_entries else None,
            'newest_entry': max(all_entries, key=lambda x: x.timestamp).timestamp.isoformat() if all_entries else None
        }
    
    def cleanup_old_logs(self) -> int:
        """Clean up old log files based on retention policy."""
        cutoff_date = datetime.utcnow() - timedelta(days=self.max_log_age_days)
        deleted_count = 0
        
        log_files = list(self.log_directory.glob("action_log_*.json"))
        log_files.extend(self.log_directory.glob("action_log_*.json.gz"))
        
        for log_file in log_files:
            try:
                # Extract date from filename
                filename = log_file.stem.replace('.json', '')  # Remove .json from .json.gz
                date_part = filename.split('_')[-1]  # Get date part
                file_date = datetime.strptime(date_part[:8], '%Y%m%d')
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")
                    
            except (ValueError, IndexError) as e:
                logger.warning(f"Could not parse date from log file {log_file}: {e}")
        
        return deleted_count
    
    def _get_session_filename(self) -> str:
        """Generate filename for current session."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"action_log_{timestamp}.json"
    
    def _save_session_log(self) -> None:
        """Save current session entries to file."""
        if not self.session_entries:
            return
        
        session_file = self.log_directory / self.current_session_file
        
        try:
            # Convert entries to dictionaries
            entries_data = [entry.to_dict() for entry in self.session_entries]
            
            # Save to file
            with open(session_file, 'w') as f:
                json.dump({
                    'session_info': {
                        'created_at': datetime.utcnow().isoformat() + 'Z',
                        'entry_count': len(entries_data),
                        'version': '1.0'
                    },
                    'entries': entries_data
                }, f, indent=2)
                
            logger.debug(f"Saved session log with {len(entries_data)} entries")
            
        except Exception as e:
            logger.error(f"Failed to save session log: {e}")
    
    def _load_log_file(self, log_file: Path) -> List[ActionLogEntry]:
        """Load entries from a log file."""
        entries = []
        
        try:
            # Handle compressed files
            if log_file.suffix == '.gz':
                with gzip.open(log_file, 'rt') as f:
                    data = json.load(f)
            else:
                with open(log_file, 'r') as f:
                    data = json.load(f)
            
            # Convert dictionary data back to ActionLogEntry objects
            for entry_data in data.get('entries', []):
                entry = self._dict_to_entry(entry_data)
                if entry:
                    entries.append(entry)
                    
        except Exception as e:
            logger.error(f"Failed to load log file {log_file}: {e}")
        
        return entries
    
    def _dict_to_entry(self, entry_data: Dict) -> Optional[ActionLogEntry]:
        """Convert dictionary data back to ActionLogEntry."""
        try:
            # Create a minimal entry and populate it
            entry = ActionLogEntry(
                entry_data['plan_id'],
                entry_data['plan_data'],
                entry_data['execution_result'],
                entry_data.get('timeline_mapping', {})
            )
            
            # Override with stored values
            entry.entry_id = entry_data['entry_id']
            entry.timestamp = datetime.fromisoformat(entry_data['timestamp'].replace('Z', '+00:00'))
            entry.checksum = entry_data.get('checksum', entry.checksum)
            
            return entry
            
        except Exception as e:
            logger.warning(f"Failed to reconstruct log entry: {e}")
            return None
    
    def _collect_entries_for_export(self, start_date: Optional[datetime],
                                  end_date: Optional[datetime]) -> List[ActionLogEntry]:
        """Collect entries matching date criteria."""
        all_entries = []
        
        # Add current session
        all_entries.extend(self.session_entries)
        
        # Load all historical logs
        log_files = list(self.log_directory.glob("action_log_*.json"))
        log_files.extend(self.log_directory.glob("action_log_*.json.gz"))
        
        for log_file in sorted(log_files):
            try:
                entries = self._load_log_file(log_file)
                all_entries.extend(entries)
            except Exception as e:
                logger.warning(f"Failed to load log file for export {log_file}: {e}")
        
        # Filter by date range
        filtered_entries = []
        for entry in all_entries:
            if start_date and entry.timestamp < start_date:
                continue
            if end_date and entry.timestamp > end_date:
                continue
            filtered_entries.append(entry)
        
        return sorted(filtered_entries, key=lambda x: x.timestamp)
    
    def _export_json(self, entries: List[ActionLogEntry], export_path: Path) -> None:
        """Export entries as JSON."""
        export_data = {
            'export_info': {
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'entry_count': len(entries),
                'format_version': '1.0'
            },
            'entries': [entry.to_dict() for entry in entries]
        }
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def _export_csv(self, entries: List[ActionLogEntry], export_path: Path) -> None:
        """Export entries as CSV."""
        fieldnames = [
            'entry_id', 'timestamp', 'plan_id', 'natural_language_prompt',
            'operation_count', 'execution_duration', 'success', 'error_message',
            'human_readable_summary'
        ]
        
        with open(export_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for entry in entries:
                writer.writerow({
                    'entry_id': entry.entry_id,
                    'timestamp': entry.timestamp.isoformat(),
                    'plan_id': entry.plan_id,
                    'natural_language_prompt': entry.natural_language_prompt,
                    'operation_count': entry.operation_count,
                    'execution_duration': entry.execution_duration,
                    'success': entry.success,
                    'error_message': entry.error_message or '',
                    'human_readable_summary': entry.get_human_readable_summary()
                })
    
    def _export_txt(self, entries: List[ActionLogEntry], export_path: Path) -> None:
        """Export entries as human-readable text."""
        with open(export_path, 'w') as f:
            f.write("Fusion 360 Co-Pilot Action Log Export\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Generated: {datetime.utcnow().isoformat()}Z\n")
            f.write(f"Total entries: {len(entries)}\n\n")
            
            for i, entry in enumerate(entries, 1):
                f.write(f"{i}. {entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
                f.write(f"   Entry ID: {entry.entry_id}\n")
                f.write(f"   Plan ID: {entry.plan_id}\n")
                f.write(f"   Prompt: {entry.natural_language_prompt}\n")
                f.write(f"   Summary: {entry.get_human_readable_summary()}\n")
                f.write(f"   Duration: {entry.execution_duration:.2f}s\n")
                f.write(f"   Status: {'Success' if entry.success else 'Failed'}\n")
                if entry.error_message:
                    f.write(f"   Error: {entry.error_message}\n")
                f.write("\n")
    
    def _prepare_replay_data(self, entry: ActionLogEntry) -> Dict:
        """Prepare entry data for replay."""
        return {
            'entry_id': entry.entry_id,
            'original_timestamp': entry.timestamp.isoformat(),
            'plan_data': entry.plan_data,
            'timeline_mapping': entry.timeline_mapping,
            'execution_result': entry.execution_result,
            'replay_notes': [
                'This is a replay of a previously executed action',
                'Timeline node references may need to be updated',
                'Verify current document state before applying'
            ]
        }


def pretty_print_action_log(entries: List[ActionLogEntry], max_entries: int = 20) -> str:
    """
    Generate a pretty-printed human-readable action log.
    
    Args:
        entries: List of action log entries
        max_entries: Maximum number of entries to include
        
    Returns:
        Formatted string representation of the action log
    """
    if not entries:
        return "No actions logged yet."
    
    # Sort by timestamp (most recent first)
    sorted_entries = sorted(entries, key=lambda x: x.timestamp, reverse=True)
    display_entries = sorted_entries[:max_entries]
    
    lines = []
    lines.append("Recent Actions:")
    lines.append("-" * 50)
    
    for i, entry in enumerate(display_entries, 1):
        timestamp = entry.timestamp.strftime('%H:%M:%S')
        status_icon = "✓" if entry.success else "✗"
        duration = f"({entry.execution_duration:.1f}s)" if entry.execution_duration > 0 else ""
        
        lines.append(f"{i:2d}) {timestamp} {status_icon} {entry.get_human_readable_summary()} {duration}")
        
        if entry.error_message:
            lines.append(f"     Error: {entry.error_message}")
    
    if len(sorted_entries) > max_entries:
        lines.append(f"... and {len(sorted_entries) - max_entries} more entries")
    
    return "\n".join(lines)


# Example usage and testing
if __name__ == "__main__":
    # Example usage
    logger = ActionLogger("test_logs")
    
    # Example plan and execution result
    test_plan = {
        "plan_id": "test_001",
        "metadata": {
            "natural_language_prompt": "Create a simple cube",
            "units": "mm"
        },
        "operations": [
            {"op_id": "op_1", "op": "create_sketch", "params": {"plane": "XY"}},
            {"op_id": "op_2", "op": "draw_rectangle", "params": {"width": {"value": 10, "unit": "mm"}, "height": {"value": 10, "unit": "mm"}}},
            {"op_id": "op_3", "op": "extrude", "params": {"distance": {"value": 10, "unit": "mm"}}}
        ]
    }
    
    test_result = {
        "success": True,
        "duration_seconds": 2.5,
        "features_created": ["sketch_1", "extrude_1"],
        "timeline_nodes": ["Timeline_Node_123", "Timeline_Node_124"]
    }
    
    # Log the action
    entry_id = logger.log_action("test_001", test_plan, test_result, {"op_1": "Timeline_Node_123", "op_3": "Timeline_Node_124"})
    
    print(f"Logged action: {entry_id}")
    
    # Export log
    export_file = logger.export_action_log('txt')
    print(f"Exported to: {export_file}")
    
    # Show statistics
    stats = logger.get_statistics()
    print(f"Statistics: {stats}")
