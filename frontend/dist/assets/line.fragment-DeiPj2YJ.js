import{S as r}from"./sindarius-gcodeviewer.es-DR34JbJy.js";import"./clipPlaneFragment-EV2Rhmy4.js";import"./logDepthDeclaration-BYzyWiC1.js";import"./logDepthFragment-CB6__cR8.js";import"./index-CfZPXLYz.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-n1Rr91tl.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
