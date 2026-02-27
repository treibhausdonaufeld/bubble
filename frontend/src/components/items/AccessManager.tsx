import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useLanguage } from '@/contexts/LanguageContext';
import {
  groupsList,
  itemsCoOwnersCreate,
  itemsCoOwnersDestroy,
  itemsCoOwnersRetrieve,
  itemsViewersCreate,
  itemsViewersDestroy,
  itemsViewersRetrieve,
  usersList,
  VisibilityEnum,
} from '@/services/django';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { X } from 'lucide-react';
import { useState } from 'react';

interface AccessEntry {
  id: string | number;
  username?: string;
  name?: string;
}

interface AccessList {
  users: AccessEntry[];
  groups: AccessEntry[];
}

interface AccessManagerProps {
  itemId: string;
  visibility: VisibilityEnum | '';
}

/** Reusable row for removing a user or group from a list. */
const AccessRow = ({ label, onRemove }: { label: string; onRemove: () => void }) => (
  <div className="flex items-center justify-between py-1 px-2 rounded bg-muted text-sm">
    <span>{label}</span>
    <Button variant="ghost" size="sm" className="h-6 w-6 p-0" onClick={onRemove}>
      <X className="h-3 w-3" />
    </Button>
  </div>
);

/** Panel for managing either co-owners or viewers. */
const AccessPanel = ({
  title,
  description,
  data,
  isLoading,
  onAddUser,
  onAddGroup,
  onRemoveUser,
  onRemoveGroup,
  mutating,
}: {
  title: string;
  description: string;
  data: AccessList | undefined;
  isLoading: boolean;
  onAddUser: (id: string | number) => void;
  onAddGroup: (id: string | number) => void;
  onRemoveUser: (id: string | number) => void;
  onRemoveGroup: (id: string | number) => void;
  mutating: boolean;
}) => {
  const { t } = useLanguage();
  const [userSearch, setUserSearch] = useState('');
  const [groupSearch, setGroupSearch] = useState('');

  const { data: allUsers } = useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const res = await usersList();
      return res.data?.results ?? [];
    },
  });

  const { data: allGroups } = useQuery({
    queryKey: ['groups'],
    queryFn: async () => {
      const res = await groupsList();
      return res.data?.results ?? [];
    },
  });

  const existingUserIds = new Set((data?.users ?? []).map(u => String(u.id)));
  const existingGroupIds = new Set((data?.groups ?? []).map(g => String(g.id)));

  const filteredUsers = (allUsers ?? []).filter(
    u =>
      !existingUserIds.has(String(u.id)) &&
      (u.username?.toLowerCase().includes(userSearch.toLowerCase()) ||
        u.name?.toLowerCase().includes(userSearch.toLowerCase())),
  );

  const filteredGroups = (allGroups ?? []).filter(
    g =>
      !existingGroupIds.has(String(g.id)) &&
      g.name?.toLowerCase().includes(groupSearch.toLowerCase()),
  );

  return (
    <div className="space-y-4">
      <div>
        <h4 className="font-medium text-sm">{title}</h4>
        <p className="text-xs text-muted-foreground">{description}</p>
      </div>

      {isLoading && <p className="text-xs text-muted-foreground">{t('common.loading')}</p>}

      {/* Current users */}
      {(data?.users ?? []).length > 0 && (
        <div className="space-y-1">
          <Label className="text-xs">{t('accessManager.users')}</Label>
          {data!.users.map(u => (
            <AccessRow
              key={`user-${u.id}`}
              label={u.username ?? String(u.id)}
              onRemove={() => onRemoveUser(u.id)}
            />
          ))}
        </div>
      )}

      {/* Current groups */}
      {(data?.groups ?? []).length > 0 && (
        <div className="space-y-1">
          <Label className="text-xs">{t('accessManager.groups')}</Label>
          {data!.groups.map(g => (
            <AccessRow
              key={`group-${g.id}`}
              label={g.name ?? String(g.id)}
              onRemove={() => onRemoveGroup(g.id)}
            />
          ))}
        </div>
      )}

      {/* Add user */}
      <div className="space-y-1">
        <Label className="text-xs">{t('accessManager.addUser')}</Label>
        <Input
          placeholder={t('accessManager.searchUsers')}
          value={userSearch}
          onChange={e => setUserSearch(e.target.value)}
          className="h-8 text-sm"
          disabled={mutating}
        />
        {userSearch.length > 0 && filteredUsers.length > 0 && (
          <div className="border rounded p-1 space-y-1 max-h-32 overflow-y-auto">
            {filteredUsers.map(u => (
              <button
                key={u.id}
                type="button"
                className="w-full text-left text-sm px-2 py-1 rounded hover:bg-muted"
                onClick={() => {
                  onAddUser(u.id);
                  setUserSearch('');
                }}
                disabled={mutating}
              >
                {u.username}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Add group */}
      <div className="space-y-1">
        <Label className="text-xs">{t('accessManager.addGroup')}</Label>
        <Input
          placeholder={t('accessManager.searchGroups')}
          value={groupSearch}
          onChange={e => setGroupSearch(e.target.value)}
          className="h-8 text-sm"
          disabled={mutating}
        />
        {groupSearch.length > 0 && filteredGroups.length > 0 && (
          <div className="border rounded p-1 space-y-1 max-h-32 overflow-y-auto">
            {filteredGroups.map(g => (
              <button
                key={g.id}
                type="button"
                className="w-full text-left text-sm px-2 py-1 rounded hover:bg-muted"
                onClick={() => {
                  onAddGroup(g.id);
                  setGroupSearch('');
                }}
                disabled={mutating}
              >
                {g.name}
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * AccessManager — lets the item owner manage co-owners and specific viewers.
 * Only renders when visibility is SPECIFIC (2) or PRIVATE (3) — though it can
 * be shown always to let the owner pre-configure access.
 */
export const AccessManager = ({ itemId, visibility }: AccessManagerProps) => {
  const { t } = useLanguage();
  const queryClient = useQueryClient();

  const coOwnersKey = ['item-co-owners', itemId];
  const viewersKey = ['item-viewers', itemId];

  const { data: coOwners, isLoading: loadingCoOwners } = useQuery({
    queryKey: coOwnersKey,
    queryFn: async () => {
      const res = await itemsCoOwnersRetrieve({ path: { id: itemId } });
      return (res.data ?? { users: [], groups: [] }) as AccessList;
    },
  });

  const { data: viewers, isLoading: loadingViewers } = useQuery({
    queryKey: viewersKey,
    queryFn: async () => {
      const res = await itemsViewersRetrieve({ path: { id: itemId } });
      return (res.data ?? { users: [], groups: [] }) as AccessList;
    },
    // Only fetch viewers when visibility is SPECIFIC
    enabled: visibility === 2,
  });

  const addCoOwnerUser = useMutation({
    mutationFn: (userId: string | number) =>
      itemsCoOwnersCreate({ path: { id: itemId }, body: { user: userId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: coOwnersKey }),
  });

  const removeCoOwnerUser = useMutation({
    mutationFn: (userId: string | number) =>
      itemsCoOwnersDestroy({ path: { id: itemId }, body: { user: userId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: coOwnersKey }),
  });

  const addCoOwnerGroup = useMutation({
    mutationFn: (groupId: string | number) =>
      itemsCoOwnersCreate({ path: { id: itemId }, body: { group: groupId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: coOwnersKey }),
  });

  const removeCoOwnerGroup = useMutation({
    mutationFn: (groupId: string | number) =>
      itemsCoOwnersDestroy({ path: { id: itemId }, body: { group: groupId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: coOwnersKey }),
  });

  const addViewerUser = useMutation({
    mutationFn: (userId: string | number) =>
      itemsViewersCreate({ path: { id: itemId }, body: { user: userId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: viewersKey }),
  });

  const removeViewerUser = useMutation({
    mutationFn: (userId: string | number) =>
      itemsViewersDestroy({ path: { id: itemId }, body: { user: userId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: viewersKey }),
  });

  const addViewerGroup = useMutation({
    mutationFn: (groupId: string | number) =>
      itemsViewersCreate({ path: { id: itemId }, body: { group: groupId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: viewersKey }),
  });

  const removeViewerGroup = useMutation({
    mutationFn: (groupId: string | number) =>
      itemsViewersDestroy({ path: { id: itemId }, body: { group: groupId } as any }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: viewersKey }),
  });

  const anyMutating =
    addCoOwnerUser.isPending ||
    removeCoOwnerUser.isPending ||
    addCoOwnerGroup.isPending ||
    removeCoOwnerGroup.isPending ||
    addViewerUser.isPending ||
    removeViewerUser.isPending ||
    addViewerGroup.isPending ||
    removeViewerGroup.isPending;

  return (
    <div className="space-y-6">
      <h3 className="text-sm font-semibold">{t('accessManager.title')}</h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Co-owners panel — always shown */}
        <AccessPanel
          title={t('accessManager.coOwnersTitle')}
          description={t('accessManager.coOwnersDescription')}
          data={coOwners}
          isLoading={loadingCoOwners}
          onAddUser={id => addCoOwnerUser.mutate(id)}
          onAddGroup={id => addCoOwnerGroup.mutate(id)}
          onRemoveUser={id => removeCoOwnerUser.mutate(id)}
          onRemoveGroup={id => removeCoOwnerGroup.mutate(id)}
          mutating={anyMutating}
        />

        {/* Viewers panel — only relevant for SPECIFIC visibility */}
        {visibility === 2 && (
          <AccessPanel
            title={t('accessManager.viewersTitle')}
            description={t('accessManager.viewersDescription')}
            data={viewers}
            isLoading={loadingViewers}
            onAddUser={id => addViewerUser.mutate(id)}
            onAddGroup={id => addViewerGroup.mutate(id)}
            onRemoveUser={id => removeViewerUser.mutate(id)}
            onRemoveGroup={id => removeViewerGroup.mutate(id)}
            mutating={anyMutating}
          />
        )}
      </div>
    </div>
  );
};
