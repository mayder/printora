import{S as n}from"./sindarius-gcodeviewer.es-D8aAAfcm.js";import"./clipPlaneFragment-XcsE7-Qo.js";import"./logDepthDeclaration-k6GQlfTZ.js";import"./logDepthFragment-BkaZ2qxN.js";import"./index-c4kO9gs2.js";const e="linePixelShader",r=`#include<clipPlaneFragmentDeclaration>
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
