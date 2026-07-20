import{S as n}from"./sindarius-gcodeviewer.es-DczbOCSj.js";import"./index-DmjJpLRD.js";const e="linePixelShader",i=`#include<clipPlaneFragmentDeclaration>
uniform vec4 color;
#ifdef LOGARITHMICDEPTH
#extension GL_EXT_frag_depth : enable
#endif
#include<logDepthDeclaration>
#define CUSTOM_FRAGMENT_DEFINITIONS
void main(void) {
#define CUSTOM_FRAGMENT_MAIN_BEGIN
#include<logDepthFragment>
#include<clipPlaneFragment>
gl_FragColor=color;
#define CUSTOM_FRAGMENT_MAIN_END
}`;n.ShadersStore[e]||(n.ShadersStore[e]=i);const a={name:e,shader:i};export{a as linePixelShader};
