import json
from typing import Optional

import boto3
import neuroglancer
from neuroglancer import ImageLayer, Viewer, ViewerState
from config import Constants

# Create local neuroglancer server
neuroglancer.set_server_bind_address(bind_address=Constants.NEUROGLANCER_IP.value, bind_port=Constants.NEUROGLANCER_PORT.value)
# TODO: start/stop server:
# https://neuroglancer-docs.web.app/python/api/index.html#server


def create_image_layer(source: str, tool_bindings: Optional[dict] = None) -> ImageLayer:
    """Creates a new ImageLayer instance"""
    if tool_bindings is None:
        return ImageLayer(source=source)
    return ImageLayer(
        source=source,
        tool_bindings=tool_bindings,
    )


def create_viewer(image_layer: ImageLayer) -> Viewer:
    """Creates a new Neuroglancer viewer instance"""
    viewer = Viewer()
    # prints the url to access the viewer
    print(viewer)
    with viewer.txn() as s:
        s.layers["image"] = image_layer
    return viewer


def create_default_viewer():
    """Creates a default Neuroglancer viewer instance for testing"""
    image_layer = create_image_layer(
        source="precomputed://gs://neuroglancer-public-data/flyem_fib-25/image",
        tool_bindings={
            "A": neuroglancer.ShaderControlTool(control="normalized"),
            "B": neuroglancer.OpacityTool(),
        },
    )
    viewer = create_viewer(image_layer=image_layer)
    return viewer

def get_viewer_url(viewer: Viewer) -> str:
    """Gets the viewer url"""
    # viewer.get_viewer_url() gets the container machine ip and port
    # We want the url that can be accessed from the browser
    return f"http://{Constants.NEUROGLANCER_VIEWER_HOST.value}:8080/v/{viewer.token}/"

def url_to_viewer_state(url: str) -> ViewerState:
    """Parses state from a Neuroglancer URL"""
    viewer_state = neuroglancer.parse_url(url)
    return viewer_state


def viewer_state_to_json_dump(viewer_state: ViewerState) -> str:
    """Converts a Neuroglancer ViewerState to JSON"""
    json_dump = neuroglancer.to_json_dump(viewer_state, indent=3)
    return json_dump


def url_to_json_dump(url: str) -> str:
    """Parses state json from a Neuroglancer URL"""
    viewer_state = url_to_viewer_state(url)
    json_dump = viewer_state_to_json_dump(viewer_state)
    return json_dump


def json_dump_to_viewer_state(json_dump: str) -> ViewerState:
    """Creates a Neuroglancer ViewerState from JSON data"""
    # convert to dict
    json_data = json.loads(json_dump)
    viewer_state = ViewerState(json_data=json_data)
    return viewer_state


def set_viewer_state(viewer: Viewer, viewer_state: ViewerState) -> None:
    """Sets the viewer state"""
    viewer.set_state(viewer_state)


def create_viewer_state() -> ViewerState:
    """Creates a new Neuroglancer ViewerState"""
    # create from: "#!s3://aind-open-data-dev-u5u0i5/SmartSPIM_660851_2023-04-03_16-25-48_stitched_2025-01-17_00-58-31/neuroglancer_config.json?"
    json_data = "#!s3://aind-open-data-dev-u5u0i5/SmartSPIM_660851_2023-04-03_16-25-48_stitched_2025-01-17_00-58-31/neuroglancer_config.json?"
    viewer_state = ViewerState(json_data=json_data)
    # viewer_state = ViewerState()
    # return viewer_state


def download_s3_state_config(s3_location: str) -> str:
    """Downloads the S3 state config file"""
    s3 = boto3.client("s3")
    # TODO: use url parse to extract bucket and key
    bucket = s3_location.split("/")[2]
    key = "/".join(s3_location.split("/")[3:])
    contents = s3.get_object(Bucket=bucket, Key=key)
    # read the file contents
    file_contents = contents["Body"].read().decode("utf-8")
    return file_contents


def get_annotations_from_state(viewer_state: ViewerState) -> list:
    """Extracts annotations from the a viewer state"""
    # For now, serialize the state to JSON and parse the annotation layer
    # There may be a better way to do this directly from the ViewerState object
    state = json.loads(neuroglancer.to_json_dump(viewer_state, indent=3))
    layers = state.get("layers", {})
    annotation_layer = None
    # If there are multiple annotation layers
    # Assume we can take the one named "annotation"
    for l in layers:
        if l.get("type") == "annotation" and l.get("name") == "annotation":
            annotation_layer = l
            break
    if annotation_layer is None:
        print("No annotation layer found in the current viewer state.")
        return []
    # print(f"Annotation layer: {annotation_layer}")
    annotations = annotation_layer.get("annotations", [])
    print(f"# Annotations found: {len(annotations)}")
    return annotations
