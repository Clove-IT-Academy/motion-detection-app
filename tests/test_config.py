import pytest
from motion_app.config import Config
from motion_app.main import main


@pytest.mark.parametrize("settings", [dict(camera_index=-1), dict(threshold=256),
    dict(threshold=True), dict(min_area=0), dict(min_area=float('nan')),
    dict(hold_seconds=float('inf')), dict(hold_seconds=-1), dict(blur_kernel=4),
    dict(morphology_kernel=0), dict(show_boxes=1)])
def test_invalid_configuration(settings):
    with pytest.raises(ValueError):
        Config(**settings)


def test_valid_boundaries():
    assert Config(threshold=0, hold_seconds=0).threshold == 0
    assert Config(threshold=255).threshold == 255


@pytest.mark.parametrize('args,code', [(['--help'], 0), (['--version'], 0),
    (['--threshold', '256'], 2), (['--hold-seconds', 'nan'], 2)])
def test_cli_without_camera(args, code):
    with pytest.raises(SystemExit) as error:
        main(args)
    assert error.value.code == code


@pytest.mark.parametrize('failure,expected', [(None, 0), (KeyboardInterrupt(), 0),
    (RuntimeError('private diagnostic'), 1)])
def test_valid_cli_and_runtime_exit(monkeypatch, capsys, failure, expected):
    from motion_app.app import Application
    def run(app):
        assert app.detector.config.show_boxes is False
        assert app.detector.config.threshold == 12
        if failure is not None:
            raise failure
    monkeypatch.setattr(Application, 'run', run)
    assert main(['--no-boxes', '--threshold', '12']) == expected
    assert 'private diagnostic' not in capsys.readouterr().err
