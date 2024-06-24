<template>
  <div>
    <!-- <input type="file" @change="uploadVideo" /> -->
    <el-upload
      action=""
      :before-upload="beforeUpload"
      :show-file-list="false"
    >
      <el-button type="primary">Click to upload video file</el-button>
    </el-upload>
    <br>
    <el-button type="primary"  @click="extractText">Start Video Analysis</el-button>
    <br>
    <div style="width: 70%; float: left;">
      <el-table :data="tableData" style="width: 100%">
        <template slot="empty">
          <span style="color: #969799;">no data</span>
        </template>
        <el-table-column label="time window (s)" width="140">
          <template slot-scope="scope">
              {{ getTimeWindow(scope.row) }}
          </template>
        </el-table-column>
        <el-table-column label="text from slides">
          <template slot-scope="scope">
              <span v-html=getOCRTextList(scope.row)></span>
          </template>
        </el-table-column>
        <el-table-column label="text from speech">
          <template slot-scope="scope">
              {{ getSpeechText(scope.row) }}
          </template>
        </el-table-column>
        <el-table-column label="screen ocr" >
          <template slot-scope="scope">
            <img :src="getImageUrl(scope.row)" alt="" style="max-width: 100%; height: auto;">
          </template>
        </el-table-column>
      </el-table>
    </div>
    <div style="width: 30%; float: right;">
      <el-card>
        <h3>MainTopics</h3>
        <p><span v-html=getMainTopics(result_dict)></span></p>
      </el-card>
    </div>
  </div>

</template>

<script>
import axios from 'axios'

export default {
  data () {
    return {
      result_dict: {}
    }
  },
  computed: {
    tableData () {
      let list = []
      Object.keys(this.result_dict).some((key) => {
        list.push(this.result_dict[key])
      })
      console.log('tableData', list)
      return list
    }
  },
  methods: {
    beforeUpload (file) {
      this.uploadVideo({ target: { files: [file] } })
      return false
    },
    uploadVideo (event) {
      const files = event.target.files
      if (!files || files.length === 0) {
        console.error('No files selected')
        return
      }
      const formData = new FormData()
      formData.append('video', files[0])

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
      this.extractTextFromBackend()
    },
    extractTextFromBackend () {
      const path = 'http://localhost:5000/api/extractText'
      axios.get(path)
        .then(response => {
          this.result_dict = response.data.result_dict
        })
        .catch(error => {
          console.log(error)
        })
    },
    prettyJson (val) {
      return JSON.stringify(val, null, 2)
    },
    getTimeWindow (dict) {
      return dict['time_window']
    },
    getOCRTextList (dict) {
      let text = ''
      for (let k in dict['ocrlist']) {
        if (dict['ocrlist'][k]['is_title'] === 1) {
          text += '<span style="color:red">' + dict['ocrlist'][k]['text'] + '</span><br/>' + '----------------------' + '<br/>'
        } else {
          text += dict['ocrlist'][k]['text'] + '<br/>' + '----------------------' + '<br/>'
        }
      }
      return text
    },
    getSpeechText (dict) {
      return dict['speech_text']
    },
    getImageUrl (dict) {
      console.log('ocrimg', dict['img'])
      return '/image/' + dict['img']
    },
    getMainTopics (val) {
      let ocrTitle = ''
      for (let index in val) {
        let dict = val[index]
        for (let k in dict['ocrlist']) {
          if (dict['ocrlist'][k]['is_title'] === 1) {
            ocrTitle += dict['ocrlist'][k]['text'] + '<br/><br/>'
          }
        }
      }
      return ocrTitle
    }
  }
}

</script>

<style scoped>
.el-table .cell {
  white-space: pre-line;
}
.el-table th, .el-table td {
  text-align: center;
}
.text-wrap {
  white-space: pre-wrap;
}
</style>
