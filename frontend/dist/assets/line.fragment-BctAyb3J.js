import{S as r}from"./sindarius-gcodeviewer.es-y544q35U.js";import"./clipPlaneFragment-baZ7XNoZ.js";import"./logDepthDeclaration-fAejHmSB.js";import"./logDepthFragment-Bi1YaV0E.js";import"./index-C65RLH7K.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-BQGxjbGj.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
