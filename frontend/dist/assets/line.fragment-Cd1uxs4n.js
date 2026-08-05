import{S as r}from"./sindarius-gcodeviewer.es-rksBcNxM.js";import"./clipPlaneFragment-C8Qm-zx0.js";import"./logDepthDeclaration-6rjYUlSQ.js";import"./logDepthFragment-P7RLESoY.js";import"./index-BDQorIVK.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-CNFEcl-l.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
