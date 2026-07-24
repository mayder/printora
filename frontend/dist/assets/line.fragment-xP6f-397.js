import{S as r}from"./sindarius-gcodeviewer.es-ybOmm6Zw.js";import"./clipPlaneFragment-DaDJ3g7d.js";import"./logDepthDeclaration-CTXvQQ4j.js";import"./logDepthFragment-BIrIq6WM.js";import"./index-D-0-qn4O.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BQGxjbGj.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
