import{S as r}from"./sindarius-gcodeviewer.es-ByZpGCWv.js";import"./clipPlaneFragment-GS6l6dhN.js";import"./logDepthDeclaration-CUPg3sna.js";import"./logDepthFragment-MoGeGTsQ.js";import"./index-rN2NPx_y.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
