<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Export Complete | Animix</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    
    <!-- Google AdSense Script -->
    <script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-YOUR_CLIENT_ID" crossorigin="anonymous"></script>
</head>
<body class="bg-slate-900 text-white min-h-screen flex items-center justify-center p-6">
    <div class="max-w-md w-full bg-slate-800 rounded-3xl p-8 shadow-2xl text-center">
        <div class="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <i class="fas fa-check text-2xl"></i>
        </div>
        <h2 class="text-2xl font-bold mb-2">Export Complete!</h2>
        <p class="text-slate-400 mb-8 text-sm">Your file has been processed and is ready.</p>

        <div class="space-y-4">
            <a href="/videos/{{ video_name }}" download class="block w-full bg-blue-600 hover:bg-blue-700 text-white font-bold py-4 rounded-xl transition-colors">
                <i class="fas fa-download mr-2"></i> Download Result
            </a>
            <a href="/" class="block w-full text-slate-400 hover:text-white text-sm font-medium py-2 transition-colors">
                Create Another Project
            </a>
        </div>

        <!-- ANIMIX AD ZONE: Result Page -->
        <div class="mt-8 border-t border-slate-700 pt-6">
            <span class="text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2 block">Advertisement</span>
            <ins class="adsbygoogle"
                 style="display:block"
                 data-ad-client="ca-pub-YOUR_CLIENT_ID"
                 data-ad-slot="YOUR_SLOT_ID"
                 data-ad-format="auto"
                 data-full-width-responsive="true"></ins>
            <script>
                 (adsbygoogle = window.adsbygoogle || []).push({});
            </script>
        </div>
    </div>
</body>
</html>
