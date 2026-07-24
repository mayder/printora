import{S as r}from"./sindarius-gcodeviewer.es-DG2Py5_f.js";import"./index-CprTTvVc.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BQGxjbGj.js";const e="passPixelShader",t=`varying vUV: vec2f;var textureSamplerSampler: sampler;var textureSampler: texture_2d<f32>;
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {fragmentOutputs.color=textureSample(textureSampler,textureSamplerSampler,input.vUV);}`;r.ShadersStoreWGSL[e]||(r.ShadersStoreWGSL[e]=t);const n={name:e,shader:t};export{n as passPixelShaderWGSL};
