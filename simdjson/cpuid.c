#include <stdint.h>

/* Straight from the Intel guide on checking CPUID. */
void cpuid(uint32_t eax, uint32_t ecx, uint32_t* abcd) {
#if defined(_MSC_VER)
    __cpuidex((int*)abcd, eax, ecx);
#else
    uint32_t ebx, edx;
# if defined( __i386__ ) && defined ( __PIC__ )
    /* in case of PIC under 32-bit EBX cannot be clobbered */
    __asm__("movl %%ebx, %%edi \n\t cpuid \n\t xchgl %%ebx, %%edi" : "=D" (ebx),
# else
    __asm__("cpuid" : "+b" (ebx),
# endif
    "+a" (eax), "+c" (ecx), "=d" (edx));
    abcd[0] = eax; abcd[1] = ebx; abcd[2] = ecx; abcd[3] = edx;
#endif
}

uint8_t check_xcr0_ymm()
{
    uint32_t xcr0;
#if defined(_MSC_VER)
    xcr0 = (uint32_t)_xgetbv(0);  /* min VS2010 SP1 compiler is required */
#else
    __asm__("xgetbv" : "=a" (xcr0) : "c" (0) : "%edx");
#endif
    return ((xcr0 & 6) == 6); /* checking if xmm and ymm state are enabled in XCR0 */
}

/*
 *  - 1 if AVX2 is enabled
 *  - 0 if unsupported by processor
 *  - -1 if it's supported but disabled
 */
int8_t can_use_avx2()
{
    uint32_t result[4];

    cpuid(0, 1, result);

    /* Can we even use xgetbv, which we need to detect AVX2 support. */
    if (result[2] & 1 << 26) {
        /* We can! Check to see if AVX2 is a supported CPU feature. */
        cpuid(7, 0, result);
        if(result[1] & 1 << 5) {
            /* It is! YMM registeres enabled by host? */
            return check_xcr0_ymm() ? 1 : -1;
        } else {
            /* Nope, no AVX2 CPU suport. */
            return 0;
        }
    } else {
        /* Can't use xgetbv, no way this machine supports AVX2. */
        return 0;
    }
}
