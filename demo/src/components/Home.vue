<template>
  <div>
    <p>upload video</p>
    <input type="file" @change="uploadVideo" />
    <p>extract text from video:</p>
    <p>{{ extractedText }}</p>
    <button @click="extractText">extract text</button>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  data () {
    return {
      extractedText: ''
    }
  },
  methods: {
    uploadVideo (event) {
      const files = event.target.files // 获取文件列表
      if (!files || files.length === 0) {
        console.error('No files selected')
        return
      }
      const formData = new FormData()
      formData.append('video', files[0]) // 使用 event.target.files 获取文件

      const path = 'http://localhost:5000/api/uploadVideo'
      axios.post(path, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
        .then(response => {
          alert('Video uploaded successfully.')
        })
        .catch(error => {
          console.error('Error uploading video:', error)
        })
    },
    extractText () {
      this.extractedText = this.extractTextFromBackend()
    },
    extractTextFromBackend () {
      const path = 'http://localhost:5000/api/extractText'
      axios.get(path)
        .then(response => {
          this.extractedText = response.data.extractedText
        })
        .catch(error => {
          console.log(error)
        })
    }
  }
}

</script>
