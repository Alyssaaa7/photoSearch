document.getElementById('displaytext').style.display = 'none';

function searchPhoto() {
  var apigClient = apigClientFactory.newClient({});
  console.log("11111111111")
  var user_message = document.getElementById('note-textarea').value;
  var body = {};
  var params = { q: user_message };
  var additionalParams = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  var additionalParams;
  apigClient
    .searchGet(params, body, additionalParams)
    .then(function (res) {

      resp_data = res.data;
      if (resp_data.results=="No Results found") {
        document.getElementById('displaytext').innerHTML =
          'Sorry could not find the image. Try another search words!' ;
        document.getElementById('displaytext').style.display = 'block';
      }

      resp_data.results.forEach(function (obj) {
        var img = new Image();
        console.log(obj);
        img.src = obj;
        img.setAttribute('class', 'banner-img');
        img.setAttribute('alt', 'effy');
        document.getElementById('displaytext').innerHTML =
          'Here are the images you try to find';
        document.getElementById('img-container').appendChild(img);
        document.getElementById('displaytext').style.display = 'block';
      });
    })
    .catch(function (result) {});
}

function getBase64(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    // reader.onload = () => resolve(reader.result)
    reader.onload = () => {
      let encoded = reader.result.replace(/^data:(.*;base64,)?/, '');
      if (encoded.length % 4 > 0) {
        encoded += '='.repeat(4 - (encoded.length % 4));
      }
      resolve(encoded);
    };
    reader.onerror = (error) => reject(error);
  });
}

function uploadPhoto() {
  var file = document.getElementById('file_path').files[0];
  const reader = new FileReader();

  var customLabels = document.getElementById("note_customtag").value
  var encoded_image = getBase64(file).then((data) => {
    console.log(data);
    var apigClient = apigClientFactory.newClient();

    var file_type = file.type + ';base64';
    console.log(file_type)
    var headers  = {
      'Content-Type': file_type,
      'x-amz-meta-customLabels': customLabels
    }
    var body = data;
    var params = {
      "object": file.name,
      'Content-Type': file_type,
      'x-amz-meta-customLabels': customLabels
    };
    console.log(note_customtag.value)
    var additionalParams = {
      "headers": headers
    };
    apigClient
      .uploadObjectPut(params, body, additionalParams)
      .then(function (res) {
        if (res.status == 200) {
          document.getElementById('uploadText').innerHTML =
            'Your image is uploaded successfully!';
          document.getElementById('uploadText').style.display = 'block';
        }
      });
  });
}