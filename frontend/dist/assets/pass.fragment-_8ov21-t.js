import{S as r}from"./sindarius-gcodeviewer.es-CZC19a0R.js";import"./index-Bzy32GBn.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BFpB96gC.js";const e="passPixelShader",t=`varying vUV: vec2f;var textureSamplerSampler: sampler;var textureSampler: texture_2d<f32>;
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {fragmentOutputs.color=textureSample(textureSampler,textureSamplerSampler,input.vUV);}`;r.ShadersStoreWGSL[e]||(r.ShadersStoreWGSL[e]=t);const n={name:e,shader:t};export{n as passPixelShaderWGSL};
