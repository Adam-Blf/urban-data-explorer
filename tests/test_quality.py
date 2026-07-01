"""Tests for data quality module and /pipeline/quality endpoint."""

from __future__ import annotations

import pytest


class TestQualityModule:
    def test_compute_quality_returns_list(self):
        from etl.silver.quality import compute_quality
        result = compute_quality()
        assert isinstance(result, list)

    def test_compute_quality_entries_have_required_keys(self):
        from etl.silver.quality import compute_quality
        result = compute_quality()
        # Must have at least the Gold dashboard and timeline datasets
        assert len(result) >= 1
        for entry in result:
            assert "dataset" in entry
            assert "checked_at" in entry
            # Either has quality metrics or an error key
            has_metrics = "completeness_pct" in entry
            has_error = "error" in entry
            assert has_metrics or has_error

    def test_completeness_pct_range(self):
        from etl.silver.quality import compute_quality
        result = compute_quality()
        for entry in result:
            if "completeness_pct" in entry:
                assert 0.0 <= entry["completeness_pct"] <= 100.0

    def test_out_of_range_non_negative(self):
        from etl.silver.quality import compute_quality
        result = compute_quality()
        for entry in result:
            if "out_of_range_count" in entry:
                assert entry["out_of_range_count"] >= 0

    def test_freshness_days_non_negative(self):
        from etl.silver.quality import compute_quality
        result = compute_quality()
        for entry in result:
            if entry.get("freshness_days") is not None:
                assert entry["freshness_days"] >= 0


class TestQualityEndpoint:
    def test_pipeline_quality_200(self, app_client):
        r = app_client.get("/pipeline/quality")
        assert r.status_code == 200

    def test_pipeline_quality_returns_list(self, app_client):
        r = app_client.get("/pipeline/quality")
        data = r.json()
        assert isinstance(data, list)

    def test_pipeline_quality_entry_schema(self, app_client):
        r = app_client.get("/pipeline/quality")
        data = r.json()
        assert len(data) >= 1
        entry = data[0]
        assert "dataset" in entry
        assert "checked_at" in entry
