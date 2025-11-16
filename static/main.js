async function uploadPhoto() {
    let input = document.getElementById("uploadInput");
    if (!input.files[0]) {
        alert("Please select an image!");
        return;
    }

    document.getElementById("status").innerText = "Processing...";
    
    let formData = new FormData();
    formData.append("photo", input.files[0]);

    let res = await fetch("/api/upload", {
        method: "POST",
        body: formData
    });

    let data = await res.json();
    console.log(data);

    document.getElementById("status").innerText =
        "Detected Faces: " + data.count;

    document.getElementById("result").style.display = "block";
    document.getElementById("annotatedImg").src = "/annotated";
    document.getElementById("downloadCsv").href = "/attendance";
}