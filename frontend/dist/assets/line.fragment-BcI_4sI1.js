import{S as r}from"./sindarius-gcodeviewer.es-BkGI4vcO.js";import"./clipPlaneFragment-BAsVF662.js";import"./logDepthDeclaration-B92eUK1k.js";import"./logDepthFragment-BPnJcGdp.js";import"./index-DzyWAtRQ.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-DljbX5Dz.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
