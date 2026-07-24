import{S as r}from"./sindarius-gcodeviewer.es-Chv9sRtI.js";import"./clipPlaneFragment-CjENHK3n.js";import"./logDepthDeclaration-D5yev9Zo.js";import"./logDepthFragment-CE4ObING.js";import"./index-BHzX1FmF.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-n1Rr91tl.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
