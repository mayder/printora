import{S as n}from"./sindarius-gcodeviewer.es-CjMGPGF_.js";import"./clipPlaneFragment-CnyCeP9t.js";import"./logDepthDeclaration-ifHF6vSh.js";import"./logDepthFragment-0DrG6-Ae.js";import"./index-DWQeZxLd.js";const e="linePixelShader",r=`#include<clipPlaneFragmentDeclaration>
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
