import{S as t}from"./sindarius-gcodeviewer.es-BfaEnEm2.js";import"./index-BReaRl7f.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-n1Rr91tl.js";const e="postprocessVertexShader",r=`attribute position: vec2<f32>;uniform scale: vec2<f32>;varying vUV: vec2<f32>;const madd=vec2(0.5,0.5);
#define CUSTOM_VERTEX_DEFINITIONS
@vertex
fn main(input : VertexInputs)->FragmentInputs {
#define CUSTOM_VERTEX_MAIN_BEGIN
vertexOutputs.vUV=(vertexInputs.position*madd+madd)*uniforms.scale;vertexOutputs.position=vec4(vertexInputs.position,0.0,1.0);
#define CUSTOM_VERTEX_MAIN_END
}
`;t.ShadersStoreWGSL[e]||(t.ShadersStoreWGSL[e]=r);const p={name:e,shader:r};export{p as postprocessVertexShaderWGSL};
