import{S as r}from"./sindarius-gcodeviewer.es-CQFRI5e8.js";import"./clipPlaneFragment-CYSAZ6QB.js";import"./logDepthDeclaration-DCpBSugD.js";import"./logDepthFragment-CVVoy4rr.js";import"./index-NHPhRzln.js";import"./react-vendor-9t-2b6dQ.js";import"./icons-n1Rr91tl.js";const e="linePixelShader",t=`#include<clipPlaneFragmentDeclaration>
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
