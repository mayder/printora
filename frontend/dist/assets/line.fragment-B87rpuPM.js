import{S as r}from"./sindarius-gcodeviewer.es-BhULCjI7.js";import"./clipPlaneFragment-DhCTZo2s.js";import"./logDepthDeclaration-B8sLeTCK.js";import"./logDepthFragment-CcWc_ABG.js";import"./index-DQ_wMnBN.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BQGxjbGj.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
