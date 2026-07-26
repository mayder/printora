import{S as r}from"./sindarius-gcodeviewer.es-DMndlKB_.js";import"./clipPlaneFragment-D3XXC_f4.js";import"./logDepthDeclaration-BnixJ9qb.js";import"./logDepthFragment-BQuzK4Dl.js";import"./index--zfn-DZd.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BFpB96gC.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
uniform color: vec4f;
#include<logDepthDeclaration>
#define CUSTOM_FRAGMENT_DEFINITIONS
@fragment
fn main(input: FragmentInputs)->FragmentOutputs {
#define CUSTOM_FRAGMENT_MAIN_BEGIN
#include<logDepthFragment>
#include<clipPlaneFragment>
fragmentOutputs.color=uniforms.color;
#define CUSTOM_FRAGMENT_MAIN_END
}`;r.ShadersStoreWGSL[e]||(r.ShadersStoreWGSL[e]=t);const S={name:e,shader:t};export{S as linePixelShaderWGSL};
