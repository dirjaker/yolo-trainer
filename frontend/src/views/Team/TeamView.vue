<template>
  <div class="view-wrapper">
    <n-grid :cols="2" :x-gap="16" :y-gap="16">
      <n-gi>
        <n-card title="团队列表" class="section-card">
          <template #header-extra>
            <n-button type="primary" size="small" @click="showCreateModal = true">创建团队</n-button>
          </template>
          <n-list bordered>
            <n-list-item v-for="team in teams" :key="team.id">
              <n-thing :title="team.name" :description="team.description || '暂无描述'">
                <template #header-extra>
                  <n-tag size="small">{{ team.member_count || 0 }} 人</n-tag>
                </template>
                <template #action>
                  <n-button size="small" @click="selectTeam(team)">管理成员</n-button>
                </template>
              </n-thing>
            </n-list-item>
            <n-empty v-if="!teams.length" description="暂无团队" />
          </n-list>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card :title="selectedTeam ? `${selectedTeam.name} - 成员管理` : '成员管理'" class="section-card">
          <template v-if="selectedTeam" #header-extra>
            <n-button type="primary" size="small" @click="showAddMemberModal = true">添加成员</n-button>
          </template>
          <template v-if="selectedTeam">
            <n-data-table :columns="memberColumns" :data="members" :bordered="false" :loading="membersLoading" />
          </template>
          <n-empty v-else description="选择团队查看成员" />
        </n-card>
      </n-gi>
    </n-grid>

    <n-modal v-model:show="showCreateModal" preset="card" title="创建团队" class="form-modal">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="团队名称">
          <n-input v-model:value="newTeam.name" placeholder="输入团队名称" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="newTeam.description" type="textarea" placeholder="团队描述（可选）" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showCreateModal = false">取消</n-button>
          <n-button type="primary" :loading="creating" @click="handleCreateTeam">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <n-modal v-model:show="showAddMemberModal" preset="card" title="添加成员" class="form-modal">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="用户ID">
          <n-input v-model:value="newMember.userId" placeholder="输入用户ID" />
        </n-form-item>
        <n-form-item label="角色">
          <n-select v-model:value="newMember.role" :options="roleOptions" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddMemberModal = false">取消</n-button>
          <n-button type="primary" :loading="addingMember" @click="handleAddMember">添加</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup>
import { ref, h, onMounted } from 'vue'
import { useMessage, NButton, NPopconfirm } from 'naive-ui'
import { createTeam, getTeams, addMember, removeMember } from '../../api/team'
import request from '../../api/request'

const message = useMessage()
const creating = ref(false)
const addingMember = ref(false)
const membersLoading = ref(false)

const teams = ref([])
const selectedTeam = ref(null)
const members = ref([])

const showCreateModal = ref(false)
const showAddMemberModal = ref(false)

const newTeam = ref({ name: '', description: '' })
const newMember = ref({ userId: '', role: 'member' })

const roleOptions = [
  { label: '管理员', value: 'admin' },
  { label: '成员', value: 'member' },
  { label: '观察者', value: 'viewer' },
]

const memberColumns = [
  { title: '用户ID', key: 'user_id' },
  { title: '用户名', key: 'username' },
  {
    title: '角色', key: 'role',
    render: (row) => {
      const map = { admin: '管理员', member: '成员', viewer: '观察者' }
      return map[row.role] || row.role
    },
  },
  {
    title: '操作', key: 'actions', width: 100,
    render: (row) =>
      h(NPopconfirm, { onPositiveClick: () => handleRemoveMember(row.user_id) }, {
        trigger: () => h(NButton, { size: 'small', type: 'error' }, { default: () => '移除' }),
        default: () => `确定移除 ${row.username || row.user_id}？`,
      }),
  },
]

onMounted(loadTeams)

async function loadTeams() {
  try {
    const res = await getTeams()
    teams.value = res.items || res || []
  } catch (e) { /* ignore */ }
}

async function selectTeam(team) {
  selectedTeam.value = team
  membersLoading.value = true
  try {
    const res = await request.get(`/teams/${team.id}/members`)
    members.value = res.items || res || []
  } catch (e) { /* ignore */ }
  membersLoading.value = false
}

async function handleCreateTeam() {
  if (!newTeam.value.name) { message.warning('请输入团队名称'); return }
  creating.value = true
  try {
    await createTeam(newTeam.value)
    message.success('创建成功')
    showCreateModal.value = false
    newTeam.value = { name: '', description: '' }
    loadTeams()
  } catch (e) {
    message.error(e?.message || '创建失败')
  }
  creating.value = false
}

async function handleAddMember() {
  if (!newMember.value.userId) { message.warning('请输入用户ID'); return }
  addingMember.value = true
  try {
    await addMember(selectedTeam.value.id, newMember.value.userId, newMember.value.role)
    message.success('添加成功')
    showAddMemberModal.value = false
    newMember.value = { userId: '', role: 'member' }
    selectTeam(selectedTeam.value)
  } catch (e) {
    message.error(e?.message || '添加失败')
  }
  addingMember.value = false
}

async function handleRemoveMember(userId) {
  try {
    await removeMember(selectedTeam.value.id, userId)
    message.success('已移除')
    selectTeam(selectedTeam.value)
  } catch (e) {
    message.error(e?.message || '移除失败')
  }
}
</script>

<style scoped>
.view-wrapper {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.view-wrapper :deep(.n-card) {
  border-radius: 14px;
}
.form-modal {
  width: 480px;
}
</style>
