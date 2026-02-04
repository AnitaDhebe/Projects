import os

def test_always_pass():
    assert True

def test_always_fail():
    assert False

def test_flaky_rerun():
    marker_file = ".rerun_marker"
    if os.path.exists(marker_file):
        # On rerun, pass this test
        os.remove(marker_file)
        assert True
    else:
        # Fail first time, create marker to simulate rerun scenario
        with open(marker_file, "w") as f:
            f.write("rerun this test")
        assert False
