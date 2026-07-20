import{S as n}from"./sindarius-gcodeviewer.es-Dy-rcHI5.js";import"./clipPlaneFragment-Bb4vSzf9.js";import"./logDepthDeclaration-BfKAezl4.js";import"./logDepthFragment-CqXJYOJb.js";import"./index-CGHMHMSm.js";const e="linePixelShader",r=`#include<clipPlaneFragmentDeclaration>
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
}`;n.ShadersStoreWGSL[e]||(n.ShadersStoreWGSL[e]=r);const m={name:e,shader:r};export{m as linePixelShaderWGSL};
