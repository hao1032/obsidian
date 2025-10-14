### Patch Google Photos Using ReVanced CLI  
使用 ReVanced CLI 打补丁 Google Photos
https://www.reddit.com/r/revancedapp/comments/1jb6b54/whats_the_plan_for_google_photos_support_in/

#### Requirements   要求

- [ReVanced CLI](https://github.com/ReVanced/revanced-cli/releases)
    
- [ReVanced Patches  ReVanced 补丁](https://github.com/ReVanced/revanced-patches/releases)
    
- [Google Photos APK](https://www.apkmirror.com/apk/google-inc/photos/variant-%7B%22arches_slug%22%3A%5B%22arm64-v8a%22%5D%7D/)
    
- [ReVanced GmsCore (microG)](https://github.com/ReVanced/GmsCore/releases) _(Required for non-root users)_  
    ReVanced GmsCore (microG) (非 root 用户必需)
    
- **Java (JDK 17+)**
    

#### Steps   步骤

1. **Prepare Files  准备文件**
    
    - Download **CLI, Patches, Google Photos APK, and GmsCore**.  
        下载 CLI、补丁、Google Photos APK 和 GmsCore。
        
    - Move them into a single folder.  
        将它们移动到一个文件夹中。
        
2. **Open CMD in Folder  
    在文件夹中打开 CMD**
    
    - **Shift + Right-click** → Select **"Open Command Prompt here"**  
        Shift + 右键单击 → 选择"在此处打开命令提示符"
        
3. **Run Patch Command  运行修补命令**
    
    java -jar revanced-cli.jar patch -p patches.rvp photos.apk --ei 27 --ei 28 --di 29
    
    - `--ei 27` → **Spoof features**  
        `--ei 27` → 欺骗功能
        
    - `--ei 28` → **GmsCore support**  
        `--ei 28` → GmsCore 支持
        
    - `--di 29` → **Exclude broken patch** (prevents crashes)  
        `--di 29` → 排除损坏的补丁（防止崩溃）
        
4. **Install Patched APK  安装修补后的 APK**
    
    - Transfer **photos-revanced.apk** to your phone and install manually.  
        将 photos-revanced.apk 传输到您的手机并手动安装。
        
5. **Install GmsCore (microG) (Non-root users only)  
    安装 GmsCore (microG) (仅限非 root 用户)**
    
    - Download & install **ReVanced GmsCore**.  
        下载并安装 ReVanced GmsCore。
        

#### Verify   验证

- **Initial Setup:  初始设置：**
    
    - Open **Google Photos** and **sign in**.  
        打开 Google Photos 并登录。
        
    - **DCIM folder is auto-selected** for backup.  
        DCIM 文件夹已自动选择用于备份。
        
    - Manually **select other folders** to back up.  
        手动选择其他文件夹进行备份。
        
- **Future Folder Additions:  
    未来文件夹添加：**
    
    - If a **new folder** needs to be uploaded, **sign in again** and manually select it.  
        如果需要上传新文件夹，请重新登录并手动选择它。
        
    - No further sign-in required for regular uploads.  
        常规上传无需再次登录。