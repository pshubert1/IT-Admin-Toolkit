# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({MAJOR}, {MINOR}, {PATCH}, 0),
    prodvers=({MAJOR}, {MINOR}, {PATCH}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [
            StringStruct(u'CompanyName', u'{COMPANY}'),
            StringStruct(u'FileDescription', u'{DESCRIPTION}'),
            StringStruct(u'FileVersion', u'{VERSION}'),
            StringStruct(u'InternalName', u'{INTERNAL_NAME}'),
            StringStruct(u'LegalCopyright', u'{COPYRIGHT}'),
            StringStruct(u'OriginalFilename', u'{FILENAME}'),
            StringStruct(u'ProductName', u'{PRODUCT_NAME}'),
            StringStruct(u'ProductVersion', u'{VERSION}'),
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)