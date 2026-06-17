import pytest
from dash import html
from api_user.visualization.layout.main_layout import create_main_layout
from api_user.visualization.layout.historical_layout import create_historical_layout
from api_user.visualization.layout.control_panel import create_control_panel
from api_user.visualization.layout.streaming_layout import create_streaming_layout


def test_create_main_layout_returns_div():
    layout = create_main_layout()
    assert isinstance(layout, html.Div)
    # check layout contains expected children
    children = getattr(layout, 'children', [])
    # at minimum should contain control panel, streaming, historical, and hidden sliders
    # check not empty and contains Divs
    assert len(children) >= 4
    for child in children:
        assert isinstance(child, html.Div)


def test_create_historical_layout_returns_div():
    layout = create_historical_layout()
    assert isinstance(layout, html.Div)
    # contains data-init-trigger and several chart containers
    assert len(layout.children) >= 5


def test_create_control_panel_returns_div():
    layout = create_control_panel()
    assert isinstance(layout, html.Div)
    # contains trading pair dropdown and date info
    assert len(layout.children) == 2


def test_create_streaming_layout_returns_div():
    layout = create_streaming_layout()
    assert isinstance(layout, html.Div)
    # contains H2, status divs, graph, store, websocket
    assert len(layout.children) >= 6
