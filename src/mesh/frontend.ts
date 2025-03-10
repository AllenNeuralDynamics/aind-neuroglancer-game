/**
 * @license
 * Copyright 2016 Google Inc.
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { ChunkState } from "#src/chunk_manager/base.js";
import type { ChunkManager } from "#src/chunk_manager/frontend.js";
import { Chunk, ChunkSource } from "#src/chunk_manager/frontend.js";
import type { VisibleLayerInfo } from "#src/layer/index.js";
import type {
  EncodedMeshData,
  MultiscaleFragmentFormat,
} from "#src/mesh/base.js";
import {
  FRAGMENT_SOURCE_RPC_ID,
  MESH_LAYER_RPC_ID,
  MULTISCALE_FRAGMENT_SOURCE_RPC_ID,
  MULTISCALE_MESH_LAYER_RPC_ID,
  VertexPositionFormat,
} from "#src/mesh/base.js";
import type { MultiscaleMeshManifest } from "#src/mesh/multiscale.js";
import {
  getMultiscaleChunksToDraw,
  getMultiscaleFragmentKey,
  validateOctree,
} from "#src/mesh/multiscale.js";
import type { PerspectivePanel } from "#src/perspective_view/panel.js";
import type {
  PerspectiveViewReadyRenderContext,
  PerspectiveViewRenderContext,
} from "#src/perspective_view/render_layer.js";
import { PerspectiveViewRenderLayer } from "#src/perspective_view/render_layer.js";
import type { ThreeDimensionalRenderLayerAttachmentState } from "#src/renderlayer.js";
import { update3dRenderLayerAttachment } from "#src/renderlayer.js";
import {
  forEachVisibleSegment,
  getObjectKey,
} from "#src/segmentation_display_state/base.js";
import type { SegmentationDisplayState3D } from "#src/segmentation_display_state/frontend.js";
import {
  forEachVisibleSegmentToDraw,
  registerRedrawWhenSegmentationDisplayState3DChanged,
  SegmentationLayerSharedObject,
} from "#src/segmentation_display_state/frontend.js";
import type { WatchableValueInterface } from "#src/trackable_value.js";
import { makeCachedDerivedWatchableValue } from "#src/trackable_value.js";
import type { Borrowed, RefCounted } from "#src/util/disposable.js";
import type { vec4 } from "#src/util/geom.js";
import {
  getFrustrumPlanes,
  mat3,
  mat3FromMat4,
  mat4,
  scaleMat3Output,
  vec3,
} from "#src/util/geom.js";
import * as matrix from "#src/util/matrix.js";
import type { Uint64 } from "#src/util/uint64.js";
import { GLBuffer } from "#src/webgl/buffer.js";
import type { GL } from "#src/webgl/context.js";
import { parameterizedEmitterDependentShaderGetter } from "#src/webgl/dynamic_shader.js";
import type { ShaderBuilder, ShaderProgram } from "#src/webgl/shader.js";
import type { RPC } from "#src/worker_rpc.js";
import { registerSharedObjectOwner } from "#src/worker_rpc.js";

const tempMat4 = mat4.create();
const tempMat3 = mat3.create();

// To validate the octrees and to determine the multiscale fragment responsible for each framebuffer
// location, set `DEBUG_MULTISCALE_FRAGMENTS=true` and also set `DEBUG_PICKING=true` in
// `src/object_picking.ts`.
const DEBUG_MULTISCALE_FRAGMENTS = false;

function copyMeshDataToGpu(
  gl: GL,
  chunk: FragmentChunk | MultiscaleFragmentChunk,
) {
  chunk.vertexBuffer = GLBuffer.fromData(
    gl,
    chunk.meshData.vertexPositions,
    gl.ARRAY_BUFFER,
    gl.STATIC_DRAW,
  );
  chunk.indexBuffer = GLBuffer.fromData(
    gl,
    chunk.meshData.indices,
    gl.ELEMENT_ARRAY_BUFFER,
    gl.STATIC_DRAW,
  );
  chunk.normalBuffer = GLBuffer.fromData(
    gl,
    chunk.meshData.vertexNormals,
    gl.ARRAY_BUFFER,
    gl.STATIC_DRAW,
  );
}

function freeGpuMeshData(chunk: FragmentChunk | MultiscaleFragmentChunk) {
  chunk.vertexBuffer.dispose();
  chunk.indexBuffer.dispose();
  chunk.normalBuffer.dispose();
}

/**
 * Decodes normal vectors in 2xSnorm8 octahedron encoding into normalized 3x32f vector.
 *
 * Zina H. Cigolle, Sam Donow, Daniel Evangelakos, Michael Mara, Morgan McGuire, and Quirin Meyer,
 * Survey of Efficient Representations for Independent Unit Vectors, Journal of Computer Graphics
 * Techniques (JCGT), vol. 3, no. 2, 1-30, 2014
 *
 * Available online http://jcgt.org/published/0003/02/01/
 */
const glsl_decodeNormalOctahedronSnorm8 = `
highp vec3 decodeNormalOctahedronSnorm8(highp vec2 e) {
  vec3 v = vec3(e.xy, 1.0 - abs(e.x) - abs(e.y));
  if (v.z < 0.0) v.xy = (1.0 - abs(v.yx)) * vec2(v.x > 0.0 ? 1.0 : -1.0, v.y > 0.0 ? 1.0 : -1.0);
  return normalize(v);
}
`;

function decodeSnorm8(x: number) {
  if (x >= 128) {
    x = x - 256;
  }
  return Math.max(-1, x / 127);
}

/**
 * Javascript implementation of normal decoding, for debugging.
 */
export function decodeNormalOctahedronSnorm8(normals: Uint8Array) {
  let n = normals.length;
  n -= 1;
  const out = new Float32Array(Math.floor(normals.length / 2) * 3);
  let outIndex = 0;
  for (let i = 0; i < n; i += 2) {
    const e0 = decodeSnorm8(normals[i]);
    const e1 = decodeSnorm8(normals[i + 1]);
    let v0 = e0;
    let v1 = e1;
    const v2 = 1.0 - Math.abs(e0) - Math.abs(e1);
    if (v2 < 0) {
      v0 = (1 - Math.abs(v1)) * (v0 > 0 ? 1 : -1);
      v1 = (1 - Math.abs(v0)) * (v1 > 0 ? 1 : -1);
    }
    const len = Math.sqrt(v0 ** 2 + v1 ** 2 + v2 ** 2);
    out[outIndex] = v0 / len;
    out[outIndex + 1] = v1 / len;
    out[outIndex + 2] = v2 / len;
    outIndex += 3;
  }
  return out;
}

interface VertexPositionFormatHandler {
  defineShader: (builder: ShaderBuilder) => void;
  bind: (
    gl: GL,
    shader: ShaderProgram,
    fragmentChunk: FragmentChunk | MultiscaleFragmentChunk,
  ) => void;
  endLayer: (gl: GL, shader: ShaderProgram) => void;
}

function getFloatPositionHandler(
  glAttributeType: number,
): VertexPositionFormatHandler {
  return {
    defineShader: (builder: ShaderBuilder) => {
      builder.addAttribute("highp vec3", "aVertexPosition");
      builder.addVertexCode(
        "highp vec3 getVertexPosition() { return aVertexPosition; }",
      );
    },
    bind(
      _gl: GL,
      shader: ShaderProgram,
      fragmentChunk: FragmentChunk | MultiscaleFragmentChunk,
    ) {
      fragmentChunk.vertexBuffer.bindToVertexAttrib(
        shader.attribute("aVertexPosition"),
        /*components=*/ 3,
        glAttributeType,
        /* normalized=*/ true,
      );
    },
    endLayer: (gl: GL, shader: ShaderProgram) => {
      gl.disableVertexAttribArray(shader.attribute("aVertexPosition"));
    },
  };
}

const vertexPositionHandlers: {
  [format: number]: VertexPositionFormatHandler;
} = {
  [VertexPositionFormat.float32]: getFloatPositionHandler(
    WebGL2RenderingContext.FLOAT,
  ),
  [VertexPositionFormat.uint16]: getFloatPositionHandler(
    WebGL2RenderingContext.UNSIGNED_SHORT,
  ),
  [VertexPositionFormat.uint10]: {
    defineShader: (builder: ShaderBuilder) => {
      builder.addAttribute("highp uint", "aVertexPosition");
      builder.addVertexCode(`
highp vec3 getVertexPosition() {
  return vec3(float(aVertexPosition & 1023u),
              float((aVertexPosition >> 10) & 1023u),
              float((aVertexPosition >> 20) & 1023u)) / 1023.0;
}
`);
    },
    bind(
      _gl: GL,
      shader: ShaderProgram,
      fragmentChunk: FragmentChunk | MultiscaleFragmentChunk,
    ) {
      fragmentChunk.vertexBuffer.bindToVertexAttribI(
        shader.attribute("aVertexPosition"),
        /*components=*/ 1,
        WebGL2RenderingContext.UNSIGNED_INT,
      );
    },
    endLayer: (gl: GL, shader: ShaderProgram) => {
      gl.disableVertexAttribArray(shader.attribute("aVertexPosition"));
    },
  },
};

export class MeshShaderManager {
  private tempLightVec = new Float32Array(4);
  private vertexPositionHandler: VertexPositionFormatHandler;
  constructor(
    public fragmentRelativeVertices: boolean,
    public vertexPositionFormat: VertexPositionFormat,
  ) {
    this.vertexPositionHandler = vertexPositionHandlers[vertexPositionFormat];
  }

  beginLayer(
    gl: GL,
    shader: ShaderProgram,
    renderContext: PerspectiveViewRenderContext,
    displayState: MeshDisplayState,
  ) {
    const { lightDirection, ambientLighting, directionalLighting } =
      renderContext;
    const lightVec = <vec3>this.tempLightVec;
    vec3.scale(lightVec, lightDirection, directionalLighting);
    lightVec[3] = ambientLighting;
    gl.uniform4fv(shader.uniform("uLightDirection"), lightVec);
    const silhouetteRendering = displayState.silhouetteRendering.value;
    if (silhouetteRendering > 0) {
      gl.uniform1f(shader.uniform("uSilhouettePower"), silhouetteRendering);
    }
  }

  setColor(gl: GL, shader: ShaderProgram, color: vec4) {
    gl.uniform4fv(shader.uniform("uColor"), color);
  }

  setPickID(gl: GL, shader: ShaderProgram, pickID: number) {
    gl.uniform1ui(shader.uniform("uPickID"), pickID);
  }

  beginModel(
    gl: GL,
    shader: ShaderProgram,
    renderContext: PerspectiveViewRenderContext,
    modelMat: mat4,
  ) {
    const { projectionParameters } = renderContext;
    gl.uniformMatrix4fv(
      shader.uniform("uModelViewProjection"),
      false,
      mat4.multiply(tempMat4, projectionParameters.viewProjectionMat, modelMat),
    );
    mat3FromMat4(tempMat3, modelMat);
    scaleMat3Output(
      tempMat3,
      tempMat3,
      projectionParameters.displayDimensionRenderInfo.canonicalVoxelFactors,
    );
    mat3.invert(tempMat3, tempMat3);
    mat3.transpose(tempMat3, tempMat3);
    gl.uniformMatrix3fv(shader.uniform("uNormalMatrix"), false, tempMat3);
  }

  drawFragmentHelper(
    gl: GL,
    shader: ShaderProgram,
    fragmentChunk: FragmentChunk | MultiscaleFragmentChunk,
    indexBegin: number,
    indexEnd: number,
  ) {
    this.vertexPositionHandler.bind(gl, shader, fragmentChunk);
    const { meshData } = fragmentChunk;
    fragmentChunk.normalBuffer.bindToVertexAttrib(
      shader.attribute("aVertexNormal"),
      /*components=*/ 2,
      WebGL2RenderingContext.BYTE,
      /*normalized=*/ true,
    );
    fragmentChunk.indexBuffer.bind();
    const { indices } = meshData;
    gl.drawElements(
      meshData.strips
        ? WebGL2RenderingContext.TRIANGLE_STRIP
        : WebGL2RenderingContext.TRIANGLES,
      indexEnd - indexBegin,
      indices.BYTES_PER_ELEMENT === 2
        ? WebGL2RenderingContext.UNSIGNED_SHORT
        : WebGL2RenderingContext.UNSIGNED_INT,
      indexBegin * indices.BYTES_PER_ELEMENT,
    );
  }

  drawFragment(gl: GL, shader: ShaderProgram, fragmentChunk: FragmentChunk) {
    const { meshData } = fragmentChunk;
    const { indices } = meshData;
    this.drawFragmentHelper(gl, shader, fragmentChunk, 0, indices.length);
  }

  drawMultiscaleFragment(
    gl: GL,
    shader: ShaderProgram,
    fragmentChunk: MultiscaleFragmentChunk,
    subChunkBegin: number,
    subChunkEnd: number,
  ) {
    const indexBegin = fragmentChunk.meshData.subChunkOffsets[subChunkBegin];
    const indexEnd = fragmentChunk.meshData.subChunkOffsets[subChunkEnd];
    this.drawFragmentHelper(gl, shader, fragmentChunk, indexBegin, indexEnd);
  }

  endLayer(gl: GL, shader: ShaderProgram) {
    this.vertexPositionHandler.endLayer(gl, shader);
    gl.disableVertexAttribArray(shader.attribute("aVertexNormal"));
  }

  makeGetter(layer: RefCounted & { gl: GL; displayState: MeshDisplayState }) {
    const silhouetteRenderingEnabled = layer.registerDisposer(
      makeCachedDerivedWatchableValue(
        (x) => x > 0,
        [layer.displayState.silhouetteRendering],
      ),
    );
    return parameterizedEmitterDependentShaderGetter(layer, layer.gl, {
      memoizeKey: `mesh/MeshShaderManager/${this.fragmentRelativeVertices}/${this.vertexPositionFormat}`,
      parameters: silhouetteRenderingEnabled,
      defineShader: (builder, silhouetteRenderingEnabled) => {
        this.vertexPositionHandler.defineShader(builder);
        builder.addAttribute("highp vec2", "aVertexNormal");
        builder.addVarying("highp vec4", "vColor");
        builder.addUniform("highp vec4", "uLightDirection");
        builder.addUniform("highp vec4", "uColor");
        builder.addUniform("highp mat3", "uNormalMatrix");
        builder.addUniform("highp mat4", "uModelViewProjection");
        builder.addUniform("highp uint", "uPickID");
        if (silhouetteRenderingEnabled) {
          builder.addUniform("highp float", "uSilhouettePower");
        }
        if (this.fragmentRelativeVertices) {
          builder.addUniform("highp vec3", "uFragmentOrigin");
          builder.addUniform("highp vec3", "uFragmentShape");
        }
        builder.addVertexCode(glsl_decodeNormalOctahedronSnorm8);
        let vertexMain = "";
        if (this.fragmentRelativeVertices) {
          vertexMain += `
highp vec3 vertexPosition = uFragmentOrigin + uFragmentShape * getVertexPosition();
highp vec3 normalMultiplier = 1.0 / uFragmentShape;
`;
        } else {
          vertexMain += `
highp vec3 vertexPosition = getVertexPosition();
highp vec3 normalMultiplier = vec3(1.0, 1.0, 1.0);
`;
        }
        vertexMain += `
gl_Position = uModelViewProjection * vec4(vertexPosition, 1.0);
vec3 origNormal = decodeNormalOctahedronSnorm8(aVertexNormal);
vec3 normal = normalize(uNormalMatrix * (normalMultiplier * origNormal));
float absCosAngle = abs(dot(normal, uLightDirection.xyz));
float lightingFactor = absCosAngle + uLightDirection.w;
vColor = vec4(lightingFactor * uColor.rgb, uColor.a);
`;
        if (silhouetteRenderingEnabled) {
          vertexMain += `
vColor *= pow(1.0 - absCosAngle, uSilhouettePower);
`;
        }
        builder.setVertexMain(vertexMain);
        builder.setFragmentMain("emit(vColor, uPickID);");
      },
    });
  }
}

export interface MeshDisplayState extends SegmentationDisplayState3D {
  silhouetteRendering: WatchableValueInterface<number>;
}

export class MeshLayer extends PerspectiveViewRenderLayer<ThreeDimensionalRenderLayerAttachmentState> {
  protected meshShaderManager;
  private getShader;
  backend: SegmentationLayerSharedObject;

  constructor(
    public chunkManager: ChunkManager,
    public source: MeshSource,
    public displayState: MeshDisplayState,
  ) {
    super();
    this.meshShaderManager = new MeshShaderManager(
      /*fragmentRelativeVertices=*/ false,
      VertexPositionFormat.float32,
    );
    this.getShader = this.meshShaderManager.makeGetter(this);

    registerRedrawWhenSegmentationDisplayState3DChanged(displayState, this);
    this.registerDisposer(
      displayState.silhouetteRendering.changed.add(this.redrawNeeded.dispatch),
    );

    const sharedObject = (this.backend = this.registerDisposer(
      new SegmentationLayerSharedObject(
        chunkManager,
        displayState,
        this.layerChunkProgressInfo,
      ),
    ));
    sharedObject.RPC_TYPE_ID = MESH_LAYER_RPC_ID;
    sharedObject.initializeCounterpartWithChunkManager({
      source: source.addCounterpartRef(),
    });
    sharedObject.visibility.add(this.visibility);
    this.registerDisposer(
      displayState.renderScaleHistogram.visibility.add(this.visibility),
    );
  }

  get isTransparent() {
    const { displayState } = this;
    return (
      displayState.objectAlpha.value < 1.0 ||
      displayState.silhouetteRendering.value > 0
    );
  }

  get transparentPickEnabled() {
    return this.displayState.transparentPickEnabled.value;
  }

  get gl() {
    return this.chunkManager.chunkQueueManager.gl;
  }

  draw(
    renderContext: PerspectiveViewRenderContext,
    attachment: VisibleLayerInfo<
      PerspectivePanel,
      ThreeDimensionalRenderLayerAttachmentState
    >,
  ) {
    if (!renderContext.emitColor && renderContext.alreadyEmittedPickID) {
      // No need for a separate pick ID pass.
      return;
    }
    const { gl, displayState, meshShaderManager } = this;
    if (displayState.objectAlpha.value <= 0.0) {
      // Skip drawing.
      return;
    }
    const modelMatrix = update3dRenderLayerAttachment(
      displayState.transform.value,
      renderContext.projectionParameters.displayDimensionRenderInfo,
      attachment,
    );
    if (modelMatrix === undefined) {
      return;
    }
    const { shader } = this.getShader(renderContext.emitter);
    if (shader === null) return;
    shader.bind();
    meshShaderManager.beginLayer(gl, shader, renderContext, this.displayState);
    meshShaderManager.beginModel(gl, shader, renderContext, modelMatrix);

    const manifestChunks = this.source.chunks;

    let totalChunks = 0;
    let presentChunks = 0;
    const { renderScaleHistogram } = this.displayState;
    const fragmentChunks = this.source.fragmentSource.chunks;

    forEachVisibleSegmentToDraw(
      displayState,
      this,
      renderContext.emitColor,
      renderContext.emitPickID ? renderContext.pickIDs : undefined,
      (objectId, color, pickIndex) => {
        const key = getObjectKey(objectId);
        const manifestChunk = manifestChunks.get(key);
        ++totalChunks;
        if (manifestChunk === undefined) return;
        ++presentChunks;
        if (renderContext.emitColor) {
          meshShaderManager.setColor(gl, shader, color!);
        }
        if (renderContext.emitPickID) {
          meshShaderManager.setPickID(gl, shader, pickIndex!);
        }
        totalChunks += manifestChunk.fragmentIds.length;

        for (const fragmentId of manifestChunk.fragmentIds) {
          const { key: fragmentKey } = this.source.getFragmentKey(
            key,
            fragmentId,
          );
          const fragment = fragmentChunks.get(fragmentKey);
          if (
            fragment !== undefined &&
            fragment.state === ChunkState.GPU_MEMORY
          ) {
            meshShaderManager.drawFragment(gl, shader, fragment);
            ++presentChunks;
          }
        }
      },
    );

    if (renderContext.emitColor) {
      renderScaleHistogram.begin(
        this.chunkManager.chunkQueueManager.frameNumberCounter.frameNumber,
      );
      renderScaleHistogram.add(
        Number.POSITIVE_INFINITY,
        Number.POSITIVE_INFINITY,
        presentChunks,
        totalChunks - presentChunks,
      );
    }
    meshShaderManager.endLayer(gl, shader);
  }

  isReady() {
    const { displayState, source } = this;
    let ready = true;
    const fragmentChunks = source.fragmentSource.chunks;
    forEachVisibleSegment(
      displayState.segmentationGroupState.value,
      (objectId) => {
        const key = getObjectKey(objectId);
        const manifestChunk = source.chunks.get(key);
        if (manifestChunk === undefined) {
          ready = false;
          return;
        }
        for (const fragmentId of manifestChunk.fragmentIds) {
          const { key: fragmentKey } = this.source.getFragmentKey(
            key,
            fragmentId,
          );
          const fragmentChunk = fragmentChunks.get(fragmentKey);
          if (
            fragmentChunk === undefined ||
            fragmentChunk.state !== ChunkState.GPU_MEMORY
          ) {
            ready = false;
            return;
          }
        }
      },
    );
    return ready;
  }

  getObjectPosition(
    id: Uint64,
    nearestTo: Float32Array,
  ): Float32Array | undefined {
    const transform = this.displayState.transform.value;
    if (transform.error !== undefined) return undefined;
    const key = getObjectKey(id);
    const chunk = this.source.chunks.get(key);
    if (chunk === undefined) return undefined;
    const { rank } = transform;
    const inverseModelToRenderLayerTransform = new Float32Array(
      transform.modelToRenderLayerTransform.length,
    );
    matrix.inverse(
      inverseModelToRenderLayerTransform,
      rank + 1,
      transform.modelToRenderLayerTransform,
      rank + 1,
      rank + 1,
    );
    const nearestPositionInModal = new Float32Array(rank);
    matrix.transformPoint(
      nearestPositionInModal,
      inverseModelToRenderLayerTransform,
      rank + 1,
      nearestTo,
      rank,
    );
    const { fragmentIds } = chunk;
    let vertexCount = 0;
    const fragmentChunks: FragmentChunk[] = [];
    for (const fragmentId of fragmentIds) {
      const { key: fragmentKey } = this.source.getFragmentKey(key, fragmentId);
      const fragmentChunk = this.source.fragmentSource.chunks.get(fragmentKey);
      if (fragmentChunk === undefined) continue;
      const { state, meshData } = fragmentChunk;
      if (
        state !== ChunkState.SYSTEM_MEMORY &&
        state !== ChunkState.GPU_MEMORY
      ) {
        continue;
      }
      vertexCount += meshData.vertexPositions.length / rank;
      fragmentChunks.push(fragmentChunk);
    }
    // Only check up to ~100,000 vertices.
    // Not exact because it restarts the interval for each fragment chunk.
    const TARGET_VERTEX_COUNT = 100 * 1000;
    const sampleRate = TARGET_VERTEX_COUNT / vertexCount;
    const sampleInterval = Math.max(1, Math.floor(1 / sampleRate));
    const closestVertex = new Float32Array(rank);
    let closestDistanceSq = Number.POSITIVE_INFINITY;
    for (const fragmentChunk of fragmentChunks) {
      const { meshData } = fragmentChunk;
      const { vertexPositions } = meshData;
      if (vertexPositions.length < rank) continue;
      for (let i = 0; i < vertexPositions.length; i += rank * sampleInterval) {
        let distanceSq = 0;
        for (let j = 0; j < rank; j++) {
          distanceSq +=
            (vertexPositions[i + j] - nearestPositionInModal[j]) ** 2;
        }
        if (distanceSq < closestDistanceSq) {
          closestDistanceSq = distanceSq;
          for (let j = 0; j < rank; j++) {
            closestVertex[j] = vertexPositions[i + j];
          }
        }
      }
    }
    if (closestDistanceSq === Number.POSITIVE_INFINITY) return undefined;
    const layerCenter = new Float32Array(rank);
    matrix.transformPoint(
      layerCenter,
      transform.modelToRenderLayerTransform,
      rank + 1,
      closestVertex,
      rank,
    );
    return layerCenter;
  }
}

export class ManifestChunk extends Chunk {
  fragmentIds: string[];

  constructor(source: MeshSource, x: any) {
    super(source);
    this.fragmentIds = x.fragmentIds;
  }
}

export class FragmentChunk extends Chunk {
  declare source: FragmentSource;
  vertexBuffer: GLBuffer;
  indexBuffer: GLBuffer;
  normalBuffer: GLBuffer;
  meshData: EncodedMeshData;

  constructor(source: FragmentSource, x: any) {
    super(source);
    this.meshData = x;
  }

  copyToGPU(gl: GL) {
    super.copyToGPU(gl);
    copyMeshDataToGpu(gl, this);
  }

  freeGPUMemory(gl: GL) {
    super.freeGPUMemory(gl);
    freeGpuMeshData(this);
  }
}

export type MeshSourceOptions = object;

export class MeshSource extends ChunkSource {
  fragmentSource = this.registerDisposer(
    new FragmentSource(this.chunkManager, this),
  );
  declare chunks: Map<string, ManifestChunk>;

  initializeCounterpart(rpc: RPC, options: any) {
    this.fragmentSource.initializeCounterpart(this.chunkManager.rpc!, {});
    options.fragmentSource = this.fragmentSource.addCounterpartRef();
    super.initializeCounterpart(rpc, options);
  }
  getChunk(x: any) {
    return new ManifestChunk(this, x);
  }
  getFragmentKey(objectKey: string, fragmentId: string) {
    return { key: `${objectKey}/${fragmentId}`, fragmentId: fragmentId };
  }
}

@registerSharedObjectOwner(FRAGMENT_SOURCE_RPC_ID)
export class FragmentSource extends ChunkSource {
  declare chunks: Map<string, FragmentChunk>;
  get key() {
    return this.meshSource.key;
  }
  constructor(
    chunkManager: ChunkManager,
    public meshSource: MeshSource,
  ) {
    super(chunkManager);
  }
  getChunk(x: any) {
    return new FragmentChunk(this, x);
  }
}

function hasFragmentChunk(
  fragmentChunks: Map<string, MultiscaleFragmentChunk>,
  objectKey: string,
  lod: number,
  chunkIndex: number,
) {
  const fragmentChunk = fragmentChunks.get(
    getMultiscaleFragmentKey(objectKey, lod, chunkIndex),
  );
  return (
    fragmentChunk !== undefined && fragmentChunk.state === ChunkState.GPU_MEMORY
  );
}

export class MultiscaleMeshLayer extends PerspectiveViewRenderLayer<ThreeDimensionalRenderLayerAttachmentState> {
  protected meshShaderManager: MeshShaderManager;
  private getShader;
  backend: SegmentationLayerSharedObject;

  constructor(
    public chunkManager: ChunkManager,
    public source: MultiscaleMeshSource,
    public displayState: MeshDisplayState,
  ) {
    super();
    this.meshShaderManager = new MeshShaderManager(
      /*fragmentRelativeVertices=*/ source.format.fragmentRelativeVertices,
      source.format.vertexPositionFormat,
    );
    this.getShader = this.meshShaderManager.makeGetter(this);

    registerRedrawWhenSegmentationDisplayState3DChanged(displayState, this);
    this.registerDisposer(
      displayState.silhouetteRendering.changed.add(this.redrawNeeded.dispatch),
    );

    const sharedObject = (this.backend = this.registerDisposer(
      new SegmentationLayerSharedObject(
        chunkManager,
        displayState,
        this.layerChunkProgressInfo,
      ),
    ));
    sharedObject.RPC_TYPE_ID = MULTISCALE_MESH_LAYER_RPC_ID;
    sharedObject.initializeCounterpartWithChunkManager({
      source: source.addCounterpartRef(),
    });
    sharedObject.visibility.add(this.visibility);
    this.registerDisposer(
      displayState.renderScaleHistogram.visibility.add(this.visibility),
    );
  }

  get isTransparent() {
    const { displayState } = this;
    return (
      displayState.objectAlpha.value < 1.0 ||
      displayState.silhouetteRendering.value > 0
    );
  }

  get transparentPickEnabled() {
    return this.displayState.transparentPickEnabled.value;
  }

  get gl() {
    return this.chunkManager.chunkQueueManager.gl;
  }

  draw(
    renderContext: PerspectiveViewRenderContext,
    attachment: VisibleLayerInfo<
      PerspectivePanel,
      ThreeDimensionalRenderLayerAttachmentState
    >,
  ) {
    if (!renderContext.emitColor && renderContext.alreadyEmittedPickID) {
      // No need for a separate pick ID pass.
      return;
    }
    const { gl, displayState, meshShaderManager } = this;
    if (displayState.objectAlpha.value <= 0.0) {
      // Skip drawing.
      return;
    }
    const modelMatrix = update3dRenderLayerAttachment(
      displayState.transform.value,
      renderContext.projectionParameters.displayDimensionRenderInfo,
      attachment,
    );
    if (modelMatrix === undefined) return;
    const { shader } = this.getShader(renderContext.emitter);
    if (shader === null) return;
    shader.bind();
    meshShaderManager.beginLayer(gl, shader, renderContext, this.displayState);

    const { renderScaleHistogram } = this.displayState;
    if (renderContext.emitColor) {
      renderScaleHistogram.begin(
        this.chunkManager.chunkQueueManager.frameNumberCounter.frameNumber,
      );
    }

    mat3FromMat4(tempMat3, modelMatrix);
    scaleMat3Output(
      tempMat3,
      tempMat3,
      renderContext.projectionParameters.displayDimensionRenderInfo
        .voxelPhysicalScales,
    );
    const scaleMultiplier = Math.abs(mat3.determinant(tempMat3)) ** (1 / 3);
    const { chunks } = this.source;
    const fragmentChunks = this.source.fragmentSource.chunks;

    const { projectionParameters } = renderContext;

    const modelViewProjection = mat4.multiply(
      mat4.create(),
      projectionParameters.viewProjectionMat,
      modelMatrix,
    );

    const clippingPlanes = getFrustrumPlanes(
      new Float32Array(24),
      modelViewProjection,
    );

    const detailCutoff = this.displayState.renderScaleTarget.value;
    const { fragmentRelativeVertices } = this.source.format;

    meshShaderManager.beginModel(gl, shader, renderContext, modelMatrix);

    let totalManifestChunks = 0;
    let presentManifestChunks = 0;

    forEachVisibleSegmentToDraw(
      displayState,
      this,
      renderContext.emitColor,
      renderContext.emitPickID ? renderContext.pickIDs : undefined,
      (objectId, color, pickIndex) => {
        const key = getObjectKey(objectId);
        const manifestChunk = chunks.get(key);
        ++totalManifestChunks;
        if (manifestChunk === undefined) return;
        ++presentManifestChunks;
        const { manifest } = manifestChunk;
        const { octree, chunkShape, chunkGridSpatialOrigin, vertexOffsets } =
          manifest;
        if (DEBUG_MULTISCALE_FRAGMENTS) {
          try {
            validateOctree(octree);
          } catch (e) {
            console.log(`invalid octree for object=${objectId}: ${e.message}`);
          }
        }
        if (renderContext.emitColor) {
          meshShaderManager.setColor(gl, shader, color!);
        }
        if (renderContext.emitPickID) {
          meshShaderManager.setPickID(gl, shader, pickIndex!);
        }
        getMultiscaleChunksToDraw(
          manifest,
          modelViewProjection,
          clippingPlanes,
          detailCutoff,
          projectionParameters.width,
          projectionParameters.height,
          (lod, chunkIndex, renderScale) => {
            const has = hasFragmentChunk(fragmentChunks, key, lod, chunkIndex);
            if (renderContext.emitColor) {
              renderScaleHistogram.add(
                manifest.lodScales[lod] * scaleMultiplier,
                renderScale,
                has ? 1 : 0,
                has ? 0 : 1,
              );
            }
            return has;
          },
          (lod, chunkIndex, subChunkBegin, subChunkEnd) => {
            const fragmentKey = getMultiscaleFragmentKey(key, lod, chunkIndex);
            const fragmentChunk = fragmentChunks.get(fragmentKey)!;
            const x = octree[5 * chunkIndex];
            const y = octree[5 * chunkIndex + 1];
            const z = octree[5 * chunkIndex + 2];
            const scale = 1 << lod;
            if (fragmentRelativeVertices) {
              gl.uniform3f(
                shader.uniform("uFragmentOrigin"),
                chunkGridSpatialOrigin[0] +
                  x * chunkShape[0] * scale +
                  vertexOffsets[lod * 3 + 0],
                chunkGridSpatialOrigin[1] +
                  y * chunkShape[1] * scale +
                  vertexOffsets[lod * 3 + 1],
                chunkGridSpatialOrigin[2] +
                  z * chunkShape[2] * scale +
                  vertexOffsets[lod * 3 + 2],
              );
              gl.uniform3f(
                shader.uniform("uFragmentShape"),
                chunkShape[0] * scale,
                chunkShape[1] * scale,
                chunkShape[2] * scale,
              );
            }
            if (DEBUG_MULTISCALE_FRAGMENTS) {
              const message = `lod=${lod}, chunkIndex=${chunkIndex}, subChunkBegin=${subChunkBegin}, subChunkEnd=${subChunkEnd}, uFragmentOrigin=${[
                chunkGridSpatialOrigin[0] +
                  x * chunkShape[0] * scale +
                  vertexOffsets[lod * 3 + 0],
                chunkGridSpatialOrigin[1] +
                  y * chunkShape[1] * scale +
                  vertexOffsets[lod * 3 + 1],
                chunkGridSpatialOrigin[2] +
                  z * chunkShape[2] * scale +
                  vertexOffsets[lod * 3 + 2],
              ]}, uFragmentShape=${[
                chunkShape[0] * scale,
                chunkShape[1] * scale,
                chunkShape[2] * scale,
              ]}`;
              const pickIndex = renderContext.pickIDs.registerUint64(
                this,
                objectId,
                1,
                message,
              );
              if (renderContext.emitPickID) {
                meshShaderManager.setPickID(gl, shader, pickIndex!);
              }
            }
            meshShaderManager.drawMultiscaleFragment(
              gl,
              shader,
              fragmentChunk,
              subChunkBegin,
              subChunkEnd,
            );
          },
        );
      },
    );
    renderScaleHistogram.add(
      Number.POSITIVE_INFINITY,
      Number.POSITIVE_INFINITY,
      presentManifestChunks,
      totalManifestChunks - presentManifestChunks,
    );
    meshShaderManager.endLayer(gl, shader);
  }

  isReady(
    renderContext: PerspectiveViewReadyRenderContext,
    attachment: VisibleLayerInfo<
      PerspectivePanel,
      ThreeDimensionalRenderLayerAttachmentState
    >,
  ) {
    const { displayState } = this;
    if (displayState.objectAlpha.value <= 0.0) {
      // Skip drawing.
      return true;
    }
    const modelMatrix = update3dRenderLayerAttachment(
      displayState.transform.value,
      renderContext.projectionParameters.displayDimensionRenderInfo,
      attachment,
    );
    if (modelMatrix === undefined) return false;
    const { chunks } = this.source;
    const fragmentChunks = this.source.fragmentSource.chunks;

    const { projectionParameters } = renderContext;
    const modelViewProjection = mat4.multiply(
      mat4.create(),
      projectionParameters.viewProjectionMat,
      modelMatrix,
    );

    const clippingPlanes = getFrustrumPlanes(
      new Float32Array(24),
      modelViewProjection,
    );

    const detailCutoff = this.displayState.renderScaleTarget.value;

    let hasAllChunks = true;

    forEachVisibleSegment(
      displayState.segmentationGroupState.value,
      (objectId) => {
        if (!hasAllChunks) return;
        const key = getObjectKey(objectId);
        const manifestChunk = chunks.get(key);
        if (manifestChunk === undefined) {
          hasAllChunks = false;
          return;
        }
        const { manifest } = manifestChunk;
        getMultiscaleChunksToDraw(
          manifest,
          modelViewProjection,
          clippingPlanes,
          detailCutoff,
          projectionParameters.width,
          projectionParameters.height,
          (lod, chunkIndex) => {
            hasAllChunks =
              hasAllChunks &&
              hasFragmentChunk(fragmentChunks, key, lod, chunkIndex);
            return hasAllChunks;
          },
          () => {},
        );
      },
    );
    return hasAllChunks;
  }

  getObjectPosition(id: Uint64): Float32Array | undefined {
    const transform = this.displayState.transform.value;
    if (transform.error !== undefined) return undefined;
    const chunk = this.source.chunks.get(getObjectKey(id));
    if (chunk === undefined) return undefined;
    const { manifest } = chunk;
    const { clipLowerBound, clipUpperBound } = manifest;
    const { rank } = transform;
    // Center position, in model coordinates.
    const modelCenter = new Float32Array(rank);
    for (let i = 0; i < 3; ++i) {
      modelCenter[i] = (clipLowerBound[i] + clipUpperBound[i]) / 2;
    }
    const layerCenter = new Float32Array(rank);
    matrix.transformPoint(
      layerCenter,
      transform.modelToRenderLayerTransform,
      rank + 1,
      modelCenter,
      rank,
    );
    return layerCenter;
  }
}

export class MultiscaleManifestChunk extends Chunk {
  manifest: MultiscaleMeshManifest;
  declare source: MultiscaleMeshSource;

  constructor(source: MultiscaleMeshSource, x: any) {
    super(source);
    this.manifest = x.manifest;
  }
}

export class MultiscaleFragmentChunk extends Chunk {
  meshData: EncodedMeshData & { subChunkOffsets: Uint32Array };
  declare source: MultiscaleFragmentSource;
  vertexBuffer: GLBuffer;
  indexBuffer: GLBuffer;
  normalBuffer: GLBuffer;

  constructor(source: MultiscaleFragmentSource, x: any) {
    super(source);
    this.meshData = x;
  }

  copyToGPU(gl: GL) {
    super.copyToGPU(gl);
    copyMeshDataToGpu(gl, this);
  }

  freeGPUMemory(gl: GL) {
    super.freeGPUMemory(gl);
    freeGpuMeshData(this);
  }
}

export interface MultiscaleMeshSourceOptions extends MeshSourceOptions {
  format: MultiscaleFragmentFormat;
}

export class MultiscaleMeshSource extends ChunkSource {
  declare OPTIONS: MultiscaleMeshSourceOptions;
  fragmentSource = this.registerDisposer(
    new MultiscaleFragmentSource(this.chunkManager, this),
  );
  declare chunks: Map<string, MultiscaleManifestChunk>;
  format: MultiscaleFragmentFormat;
  constructor(
    chunkManager: Borrowed<ChunkManager>,
    options: MultiscaleMeshSourceOptions,
  ) {
    super(chunkManager, options);
    this.format = options.format;
  }

  static encodeOptions(options: MultiscaleMeshSourceOptions) {
    return { format: options.format, ...ChunkSource.encodeOptions(options) };
  }

  initializeCounterpart(rpc: RPC, options: any) {
    this.fragmentSource.initializeCounterpart(this.chunkManager.rpc!, {});
    options.fragmentSource = this.fragmentSource.addCounterpartRef();
    options.format = this.format;
    super.initializeCounterpart(rpc, options);
  }
  getChunk(x: any) {
    return new MultiscaleManifestChunk(this, x);
  }
}

@registerSharedObjectOwner(MULTISCALE_FRAGMENT_SOURCE_RPC_ID)
export class MultiscaleFragmentSource extends ChunkSource {
  declare chunks: Map<string, MultiscaleFragmentChunk>;
  get key() {
    return this.meshSource.key;
  }
  constructor(
    chunkManager: ChunkManager,
    public meshSource: MultiscaleMeshSource,
  ) {
    super(chunkManager);
  }
  getChunk(x: any) {
    return new MultiscaleFragmentChunk(this, x);
  }
}
