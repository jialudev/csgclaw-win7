// Win7 compatibility fallbacks for delay-loaded DLLs (see .cargo/config.toml /DELAYLOAD).
// x64 has one calling convention, so zero-argument stubs safely stand in for
// any proc; callers only ever observe a failure HRESULT / FALSE.
#include <windows.h>
#include <delayimp.h>
#include <string.h>

static HRESULT WINAPI Stub_EFail(void) { return (HRESULT)0x80004005; }
static HRESULT WINAPI Stub_NoPackage(void) { return (HRESULT)0x80073D54; } // APPMODEL_ERROR_NO_PACKAGE
static int WINAPI Stub_False(void) { return 0; }
static BOOL WINAPI Stub_DeriveCapabilitySidsFromName(
    LPCWSTR name, PSID** group_sids, DWORD* group_count,
    PSID** capability_sids, DWORD* capability_count)
{
    (void)name;
    if (group_sids) *group_sids = NULL;
    if (group_count) *group_count = 0;
    if (capability_sids) *capability_sids = NULL;
    if (capability_count) *capability_count = 0;
    SetLastError(ERROR_CALL_NOT_IMPLEMENTED);
    return FALSE;
}

FARPROC WINAPI delayFailureHook(unsigned dliNotify, PDelayLoadInfo pdli)
{
    if (pdli == NULL) return NULL;

    if (dliNotify == dliFailLoadLib && pdli->szDll != NULL)
    {
        // combase.dll is Win8+; ole32 provides CoTaskMemFree on Windows 7.
        if (_stricmp(pdli->szDll, "combase.dll") == 0)
            return (FARPROC)LoadLibraryA("ole32.dll");

        // On Win7 these API-set DLLs are absent, so delayimp never reaches
        // dliFailGetProc unless we first provide a real module handle. Resolve
        // through kernel32, then let the exact-procedure fallbacks below
        // report unsupported operations. Returning NULL here instead raises
        // the fatal delay-load exception 0xC06D007E during turn/start.
        if (_stricmp(pdli->szDll, "api-ms-win-core-apiquery-l2-1-0.dll") == 0
            || _stricmp(pdli->szDll, "api-ms-win-security-base-l1-2-2.dll") == 0
            || _stricmp(pdli->szDll, "api-ms-win-core-winrt-l1-1-0.dll") == 0)
            return (FARPROC)LoadLibraryA("kernel32.dll");
    }

    if (dliNotify == dliFailGetProc && pdli->szDll != NULL && pdli->dlp.fImportByName)
    {
        const char* proc = pdli->dlp.szProcName;
        if (_stricmp(pdli->szDll, "userenv.dll") == 0
            && strcmp(proc, "DeriveAppContainerSidFromAppContainerName") == 0)
            return (FARPROC)Stub_NoPackage;
        if (_stricmp(pdli->szDll, "combase.dll") == 0
            && strcmp(proc, "CoIncrementMTAUsage") == 0)
            return (FARPROC)Stub_EFail;
        if (strstr(pdli->szDll, "api-ms-win-core-apiquery") != NULL
            && strcmp(proc, "IsApiSetImplemented") == 0)
            return (FARPROC)Stub_False;
        if (strstr(pdli->szDll, "api-ms-win-security-base") != NULL
            && strcmp(proc, "DeriveCapabilitySidsFromName") == 0)
            return (FARPROC)Stub_DeriveCapabilitySidsFromName;
        if (strstr(pdli->szDll, "api-ms-win-core-winrt") != NULL
            && strcmp(proc, "RoGetActivationFactory") == 0)
            return (FARPROC)Stub_EFail;
    }
    return NULL;
}

extern const PfnDliHook __pfnDliFailureHook2 = delayFailureHook;
