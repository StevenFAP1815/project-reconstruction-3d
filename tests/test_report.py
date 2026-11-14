import json

from recon3d.report import COLUMNS, collect_runs, summarize_run, to_markdown, write_csv


def write_meta(folder, **meta):
    folder.mkdir(parents=True)
    (folder / "meta.json").write_text(json.dumps(meta), encoding="utf-8")


def test_summarize_sfm_run_uses_stats(tmp_path):
    meta = {"object": "vaso-vidrio", "method": "colmap", "n_images": 81, "n_registered": 4,
            "runtime_s": 199.6, "scale_factor": None, "environment": {"gpu": "Tesla T4"},
            "extra": {"n_models": 1, "stats": {"n_images": 80, "registered_pct": 5.0,
                                               "n_points3d": 41, "mean_reprojection_error_px": 1.36}}}
    row = summarize_run(meta, tmp_path)
    assert row["stage"] == "SfM disperso (base)"
    assert row["n_used"] == 80 and row["registered_pct"] == 5.0
    assert row["n_points"] == 41 and row["status"] == "ok"


def test_summarize_experiment_run_reads_csv(tmp_path):
    (tmp_path / "experiments.csv").write_text(
        "config,n_images,n_registered,registered_pct,n_points3d,mean_reprojection_error_px,n_models\n"
        "A_base,68,43,63.24,5861,1.1153,2\n"
        "D_calibrada,68,68,100.0,19279,1.116,1\n", encoding="utf-8")
    meta = {"object": "caja-carton-leche", "method": "colmap-v2", "n_images": 73,
            "n_registered": 68, "extra": {"best_config": "D_calibrada", "model_sizes": [68]}}
    row = summarize_run(meta, tmp_path)
    assert row["registered_pct"] == 100 and row["n_points"] == 19279
    assert row["reprojection_error_px"] == 1.116 and row["n_models"] == 1


def test_collect_runs_orders_by_object_and_skips_calibration(tmp_path):
    write_meta(tmp_path / "vaso-vidrio" / "colmap", object="vaso-vidrio", method="colmap",
               n_images=81, n_registered=4)
    write_meta(tmp_path / "caja-carton-leche" / "colmap-mvs", object="caja-carton-leche",
               method="colmap-mvs", n_images=73, n_registered=68, scale_factor=60.1,
               extra={"n_object_points": 500000, "mean_abs_error_pct": 3.2})
    write_meta(tmp_path / "calibration" / "x", object="calibration", method="x", n_images=49)
    rows = collect_runs(tmp_path)
    assert [r["object"] for r in rows] == ["caja-carton-leche", "vaso-vidrio"]
    assert rows[0]["stage"] == "MVS + malla" and rows[0]["n_points"] == 500000

    csv_text = write_csv(rows, tmp_path / "t.csv").read_text(encoding="utf-8")
    assert csv_text.splitlines()[0] == ",".join(COLUMNS)
    table = to_markdown(rows)
    assert "| `caja-carton-leche` | `colmap-mvs` |" in table
    assert "3,20" in table and "500 000" in table
