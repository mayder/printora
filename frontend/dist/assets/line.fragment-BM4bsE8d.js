import{S as r}from"./sindarius-gcodeviewer.es-Cp5DR6FE.js";import"./clipPlaneFragment-DAU_VtlU.js";import"./logDepthDeclaration-DX566fZ6.js";import"./logDepthFragment-C6dELwK7.js";import"./index-BIlQge9Q.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
