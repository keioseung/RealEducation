streamlit.errors.StreamlitAPIException: This app has encountered an error. The original error message is redacted to prevent data leaks. Full error details have been recorded in the logs (if you're on Streamlit Cloud, click on 'Manage app' in the lower right of your app).

Traceback:
File "/mount/src/realeducation/app.py", line 697, in <module>
    selected_date = st.date_input("학습할 날짜를 선택하세요", value=date.fromisoformat(today_str), min_value=date.fromisoformat(all_dates[0]), max_value=date.fromisoformat(all_dates[-1]), key="learn_date_input")
                    ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/runtime/metrics_util.py", line 443, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/elements/widgets/time_widgets.py", line 840, in date_input
    return self._date_input(
           ~~~~~~~~~~~~~~~~^
        label=label,
        ^^^^^^^^^^^^
    ...<12 lines>...
        ctx=ctx,
        ^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/elements/widgets/time_widgets.py", line 932, in _date_input
    parsed_values = _DateInputValues.from_raw_values(
        value=value,
        min_value=min_value,
        max_value=max_value,
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/elements/widgets/time_widgets.py", line 241, in from_raw_values
    return cls(
        value=parsed_value,
    ...<2 lines>...
        max=parsed_max,
    )
File "<string>", line 7, in __init__
File "/home/adminuser/venv/lib/python3.13/site-packages/streamlit/elements/widgets/time_widgets.py", line 260, in __post_init__
    raise StreamlitAPIException(
    ...<3 lines>...
    )
