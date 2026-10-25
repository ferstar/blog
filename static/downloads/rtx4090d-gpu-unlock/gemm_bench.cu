#include <cuda_runtime.h>
#include <cuda_fp16.h>
#include <cuda_bf16.h>
#include <cublas_v2.h>
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <vector>
static void ck(cudaError_t c){if(c!=cudaSuccess){std::fprintf(stderr,"CUDA: %s\n",cudaGetErrorString(c));std::exit(2);}}
static void cb(cublasStatus_t c){if(c!=CUBLAS_STATUS_SUCCESS){std::fprintf(stderr,"cuBLAS: %d\n",(int)c);std::exit(2);}}
template<class T> T cv(float v);
template<> __half cv(float v){return __float2half_rn(v);}
template<> __nv_bfloat16 cv(float v){return __float2bfloat16_rn(v);}
template<> float cv(float v){return v;}
template<class T> void bench(cublasHandle_t h,const char *label,cudaDataType_t typ,cublasComputeType_t comp){
 const int n=8192,reps=5,iterations=20;const size_t count=(size_t)n*n;
 std::vector<T> a(count),b(count);
 for(size_t i=0;i<count;i++){a[i]=cv<T>((int(i%31)-15)/16.0f);b[i]=cv<T>((int((i*13)%29)-14)/16.0f);}
 T *da,*db;float *dc;ck(cudaMalloc(&da,count*sizeof(T)));ck(cudaMalloc(&db,count*sizeof(T)));ck(cudaMalloc(&dc,count*sizeof(float)));
 ck(cudaMemcpy(da,a.data(),count*sizeof(T),cudaMemcpyHostToDevice));ck(cudaMemcpy(db,b.data(),count*sizeof(T),cudaMemcpyHostToDevice));
 const float alpha=1,beta=0;
 auto run=[&](){cb(cublasGemmEx(h,CUBLAS_OP_N,CUBLAS_OP_N,n,n,n,&alpha,da,typ,n,db,typ,n,&beta,dc,CUDA_R_32F,n,comp,CUBLAS_GEMM_DEFAULT));};
 for(int i=0;i<10;i++)run();ck(cudaDeviceSynchronize());
 std::vector<double> values;
 for(int r=0;r<reps;r++){cudaEvent_t s,e;ck(cudaEventCreate(&s));ck(cudaEventCreate(&e));ck(cudaEventRecord(s));for(int i=0;i<iterations;i++)run();ck(cudaEventRecord(e));ck(cudaEventSynchronize(e));float ms;ck(cudaEventElapsedTime(&ms,s,e));double tf=2.0*n*n*n*iterations/(ms*1e9);values.push_back(tf);std::printf("%s sample=%d TFLOPS=%.6f ms=%.6f\n",label,r+1,tf,ms/iterations);std::fflush(stdout);ck(cudaEventDestroy(s));ck(cudaEventDestroy(e));}
 std::sort(values.begin(),values.end());std::printf("%s median_TFLOPS=%.6f n=%d samples=%d iterations=%d\n",label,values[2],n,reps,iterations);
 ck(cudaFree(da));ck(cudaFree(db));ck(cudaFree(dc));
}
int main(){cudaDeviceProp p;ck(cudaGetDeviceProperties(&p,0));std::printf("GPU=%s SMs=%d CC=%d.%d\n",p.name,p.multiProcessorCount,p.major,p.minor);cublasHandle_t h;cb(cublasCreate(&h));int v;cb(cublasGetVersion(h,&v));std::printf("cuBLAS=%d\n",v);cb(cublasSetMathMode(h,CUBLAS_DEFAULT_MATH));bench<__half>(h,"FP16_FP32",CUDA_R_16F,CUBLAS_COMPUTE_32F);bench<__nv_bfloat16>(h,"BF16_FP32",CUDA_R_16BF,CUBLAS_COMPUTE_32F);bench<float>(h,"TF32",CUDA_R_32F,CUBLAS_COMPUTE_32F_FAST_TF32);bench<float>(h,"FP32_control",CUDA_R_32F,CUBLAS_COMPUTE_32F_PEDANTIC);cb(cublasDestroy(h));}
