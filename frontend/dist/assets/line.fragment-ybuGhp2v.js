import{S as n}from"./sindarius-gcodeviewer.es-CnV60qqg.js";import"./clipPlaneFragment-p6CeYUAc.js";import"./logDepthDeclaration-D5tvYWsm.js";import"./logDepthFragment-Bc2CedND.js";import"./index-DeyTmUcD.js";const e="linePixelShader",r=`#include<clipPlaneFragmentDeclaration>
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
