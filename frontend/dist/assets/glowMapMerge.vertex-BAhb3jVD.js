import{S as t}from"./sindarius-gcodeviewer.es-D64MfATt.js";import"./index-D82qtxY1.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BFpB96gC.js";const e="glowMapMergeVertexShader",r=`attribute position: vec2f;varying vUV: vec2f;
#define CUSTOM_VERTEX_DEFINITIONS
@vertex
fn main(input : VertexInputs)->FragmentInputs {const madd: vec2f= vec2f(0.5,0.5);
#define CUSTOM_VERTEX_MAIN_BEGIN
vertexOutputs.vUV=input.position*madd+madd;vertexOutputs.position= vec4f(input.position,0.0,1.0);
#define CUSTOM_VERTEX_MAIN_END
}`;t.ShadersStoreWGSL[e]||(t.ShadersStoreWGSL[e]=r);const a={name:e,shader:r};export{a as glowMapMergeVertexShaderWGSL};
