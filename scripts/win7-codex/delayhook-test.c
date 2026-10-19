// Exercise both delay-load failure phases even on a modern Windows CI host.
#include <assert.h>
#include "delayhook.c"

static void check_missing_api_set(const char *dll, const char *proc, int returns_false)
{
    DelayLoadInfo info = {0};
    info.szDll = dll;
    info.dlp.fImportByName = TRUE;
    info.dlp.szProcName = proc;
    HMODULE module = (HMODULE)delayFailureHook(dliFailLoadLib, &info);
    assert(module != NULL);
    FARPROC fallback = delayFailureHook(dliFailGetProc, &info);
    assert(fallback != NULL);
    if (returns_false == 2)
    {
        PSID* groups = (PSID*)1;
        PSID* capabilities = (PSID*)1;
        DWORD group_count = 1, capability_count = 1;
        typedef BOOL (WINAPI *DeriveCapabilities)(LPCWSTR, PSID**, DWORD*, PSID**, DWORD*);
        SetLastError(ERROR_SUCCESS);
        BOOL result = ((DeriveCapabilities)fallback)(L"fixture", &groups, &group_count, &capabilities, &capability_count);
        assert(result == FALSE);
        assert(GetLastError() == ERROR_CALL_NOT_IMPLEMENTED);
        assert(groups == NULL && capabilities == NULL);
        assert(group_count == 0 && capability_count == 0);
    }
    else if (returns_false)
        assert(((int (WINAPI *)(void))fallback)() == FALSE);
    else
        assert(FAILED(((HRESULT (WINAPI *)(void))fallback)()));
    FreeLibrary(module);
}

int main(void)
{
    check_missing_api_set("api-ms-win-core-apiquery-l2-1-0.dll", "IsApiSetImplemented", 1);
    check_missing_api_set("api-ms-win-security-base-l1-2-2.dll", "DeriveCapabilitySidsFromName", 2);
    check_missing_api_set("api-ms-win-core-winrt-l1-1-0.dll", "RoGetActivationFactory", 0);
    DelayLoadInfo unknown = {0};
    unknown.szDll = "unknown-library.dll";
    unknown.dlp.fImportByName = TRUE;
    unknown.dlp.szProcName = "UnknownProcedure";
    assert(delayFailureHook(dliFailLoadLib, &unknown) == NULL);
    assert(delayFailureHook(dliFailGetProc, &unknown) == NULL);
    return 0;
}
