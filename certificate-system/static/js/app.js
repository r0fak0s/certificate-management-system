function openPreview(url) {
    document.getElementById("previewFrame").src = url;
    document.getElementById("previewModal").style.display = "block";
}

function closeModal() {
    document.getElementById("previewModal").style.display = "none";
}
function openRegistrant(id) {
    fetch(`/registrant/${id}`)
        .then(res => res.text())
        .then(html => {
            document.getElementById("registrantDetails").innerHTML = html;
            document.getElementById("registrantModal").style.display = "block";
        });
}

function closeRegistrant() {
    document.getElementById("registrantModal").style.display = "none";
}
