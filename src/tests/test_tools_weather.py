from src.tools.get_weather import GetWeatherInput, get_weather


def test_get_weather_has_summary():
    out = get_weather(GetWeatherInput(location="Berlin", month="June"))
    assert out.avg_high_c >= out.avg_low_c
    assert "Typical" in out.summary

