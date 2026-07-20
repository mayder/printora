import{S as n}from"./sindarius-gcodeviewer.es-pv85-mby.js";import"./clipPlaneFragment-3NARs5BV.js";import"./logDepthDeclaration-BSDx2k_z.js";import"./logDepthFragment-C6RfZFlm.js";import"./index-CJVbz11A.js";const e="linePixelShader",r=`#include<clipPlaneFragmentDeclaration>
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
