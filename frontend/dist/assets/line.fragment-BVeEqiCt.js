import{S as r}from"./sindarius-gcodeviewer.es-C2v8Z_nw.js";import"./clipPlaneFragment-BNa09tHs.js";import"./logDepthDeclaration-Bs0OxuS8.js";import"./logDepthFragment-CJHmedBl.js";import"./index-CjHpYonA.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-DljbX5Dz.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
