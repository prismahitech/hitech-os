#!/usr/bin/env node
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const terminalRoot = path.resolve(fileURLToPath(new URL("..", import.meta.url)));
const cloudRoot = path.join(terminalRoot, "Prisma Cloud Ctr");
const playwrightRoot = process.env.CC_PLAYWRIGHT_ROOT || "playwright";
const { chromium } = createRequire(import.meta.url)(playwrightRoot);
const VIEWPORTS = [{name:"desktop",width:1440,height:1000},{name:"mobile",width:390,height:844}];
const SURFACES = ["command","customers","entitlements","billing","fleet","provisioning","customer-setup","contracts","operations","support","security","tablet-lab","system"];

function json(res,status,payload){const body=JSON.stringify(payload);res.writeHead(status,{"content-type":"application/json; charset=utf-8","cache-control":"no-store"});res.end(body);}
function safePath(requestPath){const decoded=decodeURIComponent((requestPath||"/").split("?")[0]||"/");const candidate=path.normalize(decoded==="/" ? "/internal/web/cloud_command_center.html" : decoded);const full=path.resolve(cloudRoot,"."+candidate);if(full!==cloudRoot&&!full.startsWith(cloudRoot+path.sep))return null;return full;}
function apiPayload(url,method){
  if(url==="/api/health") return {ok:true,overall:"OK",status:200,blockers:0,dbHealth:"D1_BOUND",modules:[{id:"cloud-saas",name:"Cloud SaaS",status:"CLOUD_LIVE",http:{ok:true,statusCode:200,service:"prisma-cloud-semilla",version:"0.2.0-prisma-cloud-semilla-routing"}}]};
  if(url==="/api/runtime") return {ok:true,status:"LOCAL_READY",events:[]};
  if(url==="/api/contract") return {ok:true,status:"READY",modules:[{id:"cloud-center",status:"READY",port:3160}]};
  if(url==="/api/command-center/bootstrap") return {ok:true,status:"READY",modules:[]};
  if(url==="/api/licflow4/bridge/status") return {ok:true,bridgeAvailable:false,adminTokenPresent:false,tokenMode:"presence-only",mutationMode:"simulation"};
  if(url==="/api/license-ops/latest") return {ok:true,license:null};
  if(url==="/api/cloud-saas/summary") return {ok:true,cloud:{status:"CLOUD_LIVE",worker:"prisma-cloud-semilla",d1:"prisma_cloud_semilla",routeStatus:"READ_ONLY"},derived:{tenantCount:0,licenseCount:0,deviceCount:0,setupCount:0,claimCount:0},admin:{tokenPresent:false,tokenMode:"presence-only"},endpoints:[],licflow3Contract:{status:"LIVE",routes:[]}};
  if(url==="/api/support/catalog") return {ok:true,items:[]};
  if(url==="/api/support/search") return {ok:true,events:[],reconciliation:[]};
  if(url==="/api/command-center/other" && method==="POST") return {ok:true,status:"SIMULATED",mutationMode:"simulation",safeToMutate:false,secretsExposed:false};
  return {ok:true,status:"NOT_CONNECTED",mutationMode:"simulation",safeToMutate:false,secretsExposed:false};
}
function contentType(file){if(file.endsWith(".html"))return"text/html; charset=utf-8";if(file.endsWith(".js"))return"text/javascript; charset=utf-8";if(file.endsWith(".css"))return"text/css; charset=utf-8";if(file.endsWith(".json"))return"application/json; charset=utf-8";if(file.endsWith(".svg"))return"image/svg+xml";return"application/octet-stream";}

async function main(){
 const server=http.createServer((req,res)=>{const url=new URL(req.url||"/","http://127.0.0.1");if(url.pathname.startsWith("/api/")){json(res,200,apiPayload(url.pathname,req.method||"GET"));return;}const file=safePath(url.pathname);if(!file||!fs.existsSync(file)||!fs.statSync(file).isFile()){json(res,404,{ok:false,status:"NOT_FOUND"});return;}res.writeHead(200,{"content-type":contentType(file),"cache-control":"no-store"});fs.createReadStream(file).pipe(res);});
 await new Promise((resolve,reject)=>{server.listen(0,"127.0.0.1",resolve);server.once("error",reject);});
 const addr=server.address();const baseUrl="http://127.0.0.1:"+addr.port;const target=baseUrl+"/internal/web/cloud_command_center.html#command";
 const result={ok:false,verifier:"verify-cloud-center-browser-runtime-01",generatedAt:new Date().toISOString(),target,surfaces:SURFACES.length,profiles:[],errors:[],resultCode:"FAIL_CLOUD_CENTER_BROWSER_RUNTIME"};
 const browser=await chromium.launch({headless:true});
 try{
  for(const spec of VIEWPORTS){
   const context=await browser.newContext({viewport:{width:spec.width,height:spec.height}});const page=await context.newPage();const consoleErrors=[];const pageErrors=[];const badResponses=[];
   page.on("console",m=>{if(m.type()==="error")consoleErrors.push(m.text())});page.on("pageerror",e=>pageErrors.push(String(e)));page.on("response",r=>{if(r.url().startsWith(baseUrl)&&r.status()>=400)badResponses.push({url:r.url(),status:r.status()})});
   const response=await page.goto(target,{waitUntil:"networkidle",timeout:30000});
   if(!response||!response.ok())throw new Error(spec.name+": document HTTP "+(response&&response.status()));
   await page.waitForSelector("#surfaceRoot",{timeout:10000});
   if((await page.title())!=="Prisma Cloud Center")throw new Error(spec.name+": title drift");
   const surfaces=await page.locator("[data-surface]").evaluateAll(ns=>ns.map(n=>n.getAttribute("data-surface")));
   const missing=SURFACES.filter(x=>!surfaces.includes(x));if(missing.length)throw new Error(spec.name+": missing surfaces "+missing.join(","));
   for(const surface of SURFACES){await page.locator("[data-surface=\""+surface+"\"]").click();await page.waitForTimeout(35);const hash=await page.evaluate(()=>location.hash.replace(/^#/,""));if(hash!==surface)throw new Error(spec.name+": "+surface+" -> "+hash);const title=await page.locator("#surfaceTitle").innerText();const text=await page.locator("#surfaceRoot").innerText();if(!title.trim()||!text.trim())throw new Error(spec.name+": blank surface "+surface);}
   const bodyText=await page.locator("body").innerText();if(/PRISMA_ADMIN_TOKEN=|Bearer\s+[A-Za-z0-9._-]{16,}/i.test(bodyText))throw new Error(spec.name+": token-shaped content rendered");
   if(badResponses.length)throw new Error(spec.name+": unexpected HTTP errors "+JSON.stringify(badResponses));
   if(consoleErrors.length||pageErrors.length)throw new Error(spec.name+": console/page errors console="+consoleErrors.length+" page="+pageErrors.length);
   result.profiles.push({name:spec.name,viewport:spec,surfaceCount:surfaces.length,finalSurface:await page.evaluate(()=>location.hash.replace(/^#/,""))});
   await context.close();
  }
  result.ok=true;result.resultCode="PASS_CLOUD_CENTER_BROWSER_RUNTIME";
 }catch(error){result.errors.push(String(error&&error.stack||error));}
 finally{await browser.close();server.close();}
 console.log(JSON.stringify(result,null,2));process.exit(result.ok?0:1);
}
main().catch(e=>{console.error(e);process.exit(1);});
