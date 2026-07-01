"""Gold layer - datamarts agreges et metriques pipeline.

Responsabilites :
- metrics.py : enregistrement des metriques de pipeline (record_stage)
               et lecture pour le dashboard de monitoring (load_metrics)
"""

from .metrics import record_stage, load_metrics

__all__ = ["record_stage", "load_metrics"]
