"""
Artifact Collector - Essential for production debugging
Captures screenshots, logs, traces for every job
"""
import os
import json
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import zipfile
import io


@dataclass
class JobArtifact:
    """Artifact data for a job"""
    job_id: str
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    timeline: List[Dict] = field(default_factory=list)
    screenshots: List[Dict] = field(default_factory=list)  # {name, base64, timestamp}
    context: Dict = field(default_factory=dict)
    errors: List[Dict] = field(default_factory=list)
    final_state: str = ""
    success: bool = False


class ArtifactCollector:
    """
    Collects artifacts for debugging failed jobs

    Artifacts per job:
    - timeline.log (state + timestamp)
    - error.png (screenshot on fail)
    - context.json (job input + final state)
    - trace.zip (everything bundled)
    """

    def __init__(self, storage_dir: str = None):
        self.storage_dir = storage_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'artifacts'
        )
        self._ensure_dir()
        self.current_artifact: Optional[JobArtifact] = None

    def _ensure_dir(self):
        """Ensure storage directory exists"""
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)

    def start_job(self, job_id: str, context: Dict = None):
        """Start collecting artifacts for a job"""
        self.current_artifact = JobArtifact(
            job_id=job_id,
            context=context or {}
        )

    def add_timeline_entry(self, state: str, success: bool,
                          duration_ms: int, details: Dict = None):
        """Add entry to timeline"""
        if not self.current_artifact:
            return

        self.current_artifact.timeline.append({
            'state': state,
            'success': success,
            'duration_ms': duration_ms,
            'timestamp': datetime.now().isoformat(),
            'details': details or {}
        })

    def add_screenshot(self, name: str, base64_data: str):
        """Add screenshot"""
        if not self.current_artifact:
            return

        self.current_artifact.screenshots.append({
            'name': name,
            'data': base64_data,
            'timestamp': datetime.now().isoformat()
        })

    def add_error(self, error_type: str, message: str,
                 state: str = None, stacktrace: str = None):
        """Add error entry"""
        if not self.current_artifact:
            return

        self.current_artifact.errors.append({
            'type': error_type,
            'message': message,
            'state': state,
            'stacktrace': stacktrace,
            'timestamp': datetime.now().isoformat()
        })

    def set_final_state(self, state: str, success: bool):
        """Set final job state"""
        if not self.current_artifact:
            return

        self.current_artifact.final_state = state
        self.current_artifact.success = success

    def finish_job(self, save: bool = True) -> Optional[str]:
        """Finish collecting and optionally save artifacts"""
        if not self.current_artifact:
            return None

        artifact = self.current_artifact
        self.current_artifact = None

        if save:
            return self._save_artifact(artifact)
        return None

    def _save_artifact(self, artifact: JobArtifact) -> str:
        """Save artifact to disk"""
        # Create job directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        job_dir = os.path.join(
            self.storage_dir,
            f"{artifact.job_id}_{timestamp}"
        )
        os.makedirs(job_dir, exist_ok=True)

        # Save timeline.log
        timeline_path = os.path.join(job_dir, 'timeline.log')
        with open(timeline_path, 'w', encoding='utf-8') as f:
            for entry in artifact.timeline:
                status = "✓" if entry['success'] else "✗"
                f.write(f"[{entry['timestamp']}] {status} {entry['state']} "
                       f"({entry['duration_ms']}ms)\n")
                if entry.get('details'):
                    f.write(f"    Details: {json.dumps(entry['details'], ensure_ascii=False)}\n")

        # Save screenshots
        for i, ss in enumerate(artifact.screenshots):
            ss_path = os.path.join(job_dir, f"{ss['name']}_{i}.png")
            try:
                img_data = base64.b64decode(ss['data'])
                with open(ss_path, 'wb') as f:
                    f.write(img_data)
            except:
                pass

        # Save context.json
        context_path = os.path.join(job_dir, 'context.json')
        context_data = {
            'job_id': artifact.job_id,
            'created_at': artifact.created_at,
            'final_state': artifact.final_state,
            'success': artifact.success,
            'context': artifact.context,
            'errors': artifact.errors,
            'timeline_summary': [
                {
                    'state': e['state'],
                    'success': e['success'],
                    'duration_ms': e['duration_ms']
                }
                for e in artifact.timeline
            ]
        }
        with open(context_path, 'w', encoding='utf-8') as f:
            json.dump(context_data, f, indent=2, ensure_ascii=False)

        # Save errors.log if any errors
        if artifact.errors:
            errors_path = os.path.join(job_dir, 'errors.log')
            with open(errors_path, 'w', encoding='utf-8') as f:
                for error in artifact.errors:
                    f.write(f"[{error['timestamp']}] {error['type']}: {error['message']}\n")
                    if error.get('state'):
                        f.write(f"    State: {error['state']}\n")
                    if error.get('stacktrace'):
                        f.write(f"    Stacktrace:\n{error['stacktrace']}\n")
                    f.write("\n")

        # Create trace.zip
        zip_path = os.path.join(job_dir, 'trace.zip')
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for root, dirs, files in os.walk(job_dir):
                for file in files:
                    if file != 'trace.zip':
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, job_dir)
                        zf.write(file_path, arcname)

        return job_dir

    def get_artifact_as_bytes(self, artifact: JobArtifact) -> bytes:
        """Get artifact as zip bytes (for sending to dev)"""
        buffer = io.BytesIO()

        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Timeline
            timeline_content = ""
            for entry in artifact.timeline:
                status = "✓" if entry['success'] else "✗"
                timeline_content += f"[{entry['timestamp']}] {status} {entry['state']} ({entry['duration_ms']}ms)\n"
            zf.writestr('timeline.log', timeline_content)

            # Context
            context_data = {
                'job_id': artifact.job_id,
                'created_at': artifact.created_at,
                'final_state': artifact.final_state,
                'success': artifact.success,
                'context': artifact.context,
                'errors': artifact.errors
            }
            zf.writestr('context.json', json.dumps(context_data, indent=2, ensure_ascii=False))

            # Screenshots
            for i, ss in enumerate(artifact.screenshots):
                try:
                    img_data = base64.b64decode(ss['data'])
                    zf.writestr(f"{ss['name']}_{i}.png", img_data)
                except:
                    pass

        buffer.seek(0)
        return buffer.read()

    def cleanup_old_artifacts(self, max_age_days: int = 7):
        """Remove old artifacts to save disk space"""
        import shutil
        from datetime import timedelta

        cutoff = datetime.now() - timedelta(days=max_age_days)

        for item in os.listdir(self.storage_dir):
            item_path = os.path.join(self.storage_dir, item)
            if os.path.isdir(item_path):
                try:
                    # Parse timestamp from directory name
                    parts = item.rsplit('_', 2)
                    if len(parts) >= 2:
                        date_str = parts[-2]
                        time_str = parts[-1]
                        item_time = datetime.strptime(
                            f"{date_str}_{time_str}",
                            '%Y%m%d_%H%M%S'
                        )
                        if item_time < cutoff:
                            shutil.rmtree(item_path)
                except:
                    pass

    def get_failed_jobs(self, limit: int = 20) -> List[Dict]:
        """Get list of failed jobs with their artifacts"""
        failed = []

        for item in sorted(os.listdir(self.storage_dir), reverse=True):
            if len(failed) >= limit:
                break

            item_path = os.path.join(self.storage_dir, item)
            context_path = os.path.join(item_path, 'context.json')

            if os.path.exists(context_path):
                try:
                    with open(context_path, 'r', encoding='utf-8') as f:
                        context = json.load(f)
                        if not context.get('success'):
                            failed.append({
                                'path': item_path,
                                'job_id': context.get('job_id'),
                                'created_at': context.get('created_at'),
                                'final_state': context.get('final_state'),
                                'errors': context.get('errors', [])
                            })
                except:
                    pass

        return failed
