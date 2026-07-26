import{S as r}from"./sindarius-gcodeviewer.es-6_EuFkS-.js";import"./clipPlaneFragment-D-USUKfK.js";import"./logDepthDeclaration-CNf0orAT.js";import"./logDepthFragment-2-s56B8E.js";import"./index-CymUv5eE.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-n1Rr91tl.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
