import json
from typing import Optional
import neuroglancer
from neuroglancer import Viewer, ImageLayer, ViewerState
import boto3

# Create local neuroglancer server
ip = 'localhost'  # or public IP of the machine for sharable display
port = 8080       # change to an unused port number
neuroglancer.set_server_bind_address(bind_address=ip, bind_port=port)
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
  s3 = boto3.client('s3')
  # TODO: use url parse to extract bucket and key
  bucket = s3_location.split('/')[2]
  key = '/'.join(s3_location.split('/')[3:])
  contents = s3.get_object(Bucket=bucket, Key=key)
  # read the file contents
  file_contents = contents['Body'].read().decode('utf-8')
  return file_contents