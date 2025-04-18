import panel as pn

pn.extension()

# our test dataset
# path = "#!s3://aind-open-data-dev-u5u0i5/SmartSPIM_660851_2023-04-03_16-25-48_stitched_2025-01-17_00-58-31/neuroglancer_config.json?"
# domain = "http://52.43.100.13:8080"
# # domain = "https://neuroglancer-demo.appspot.com"
# url = f"{domain}/{path}"

# sharmi hackathon example dataset
# url = "http://tinyurl.com/2td3vbmc"
url = "http://localhost:8080"

# neuroglancer pane
iframe_html = f'<iframe id="neuroglancer-pane" src="{url}" style="height:100%; width:100%" frameborder="0"></iframe>'
neuroglancer_pane = pn.pane.HTML(
    iframe_html,
    sizing_mode="stretch_width",
    height=1000,
)

# test pane
test_html = f'<div id="test">Hello Test</div>'
test_pane = pn.pane.HTML(
    test_html,
    sizing_mode="stretch_width",
    height=1000,
)

# TRYING TO GET THE IFRAME URL
# TextInput widget to display the iframe URL
iframe_url_display = pn.widgets.TextInput(name="Iframe URL", value="", disabled=True)

# Button with JavaScript callback to update the TextInput value
button = pn.widgets.Button(name="Get Iframe URL", button_type="primary")
button.js_on_click(
  args={"iframe_url_display": iframe_url_display},
  code="""
  console.log('Button clicked!');
  var test = document.getElementById('test');
  console.log(test);
  var iframe = document.getElementById('#neuroglancer-pane');
  iframe_url_display.value = iframe.src;
  console.log(iframe);
  console.log(iframe.src);
  """
)


# Entry point for the Panel app
panel_object = pn.Column(
    "Hello World",
    button,
    iframe_url_display,
    test_pane,
    neuroglancer_pane,
).servable(title="Neuroglancer Demo")