# Tenant boundaries and actions

## Business write delegation

Classify the write before choosing the component. Do not create an action if it
is just a model update or create. A page that saves ordinary article fields can
use native CRUD with validation, policy checks and trusted actor/tenant context.
This remains true in a DDD application.

Business workflows delegate to an owning action, in Application in a layered
design. For example, article publication that checks eligibility and coordinates
a state change with an external effect belongs in PublishArticle. Simple
creation/editing does not automatically
need CreateArticle/UpdateArticle. The Filament page or UI Action owns interaction,
form validation and feedback; the business action owns workflow orchestration
and invokes the domain's rules.
Do not invent effects or rules to turn a plain save into an action.

When delegating to an action, replace persistence using the installed version's supported
extension point. Filament 5 exposes handleRecordCreation on the Create page and
handleRecordUpdate on the Edit page; modal CreateAction/EditAction expose using.
Return the saved model expected by the framework. Verify the corresponding
extension point for delete, restore, relation and bulk operations when requested.
Calling a writing action from afterCreate/afterSave leaves the default write in
place and can duplicate effects or bypass the action's preconditions.

Trace relationship saving and inline editable controls too: replacing the primary
record save does not establish ownership of every related write. Route the
feature's workflow changes through their owning actions while retaining native
Filament authorization, form lifecycle and transaction behavior. Test the business
operation and a relevant UI-to-operation path, including rejection with no
unauthorized write. UI-only changes and list/view pages require no new write action.

Sources: Filament 5 [record creation](https://filamentphp.com/docs/5.x/resources/creating-records),
[record editing](https://filamentphp.com/docs/5.x/resources/editing-records),
[modal creation](https://filamentphp.com/docs/5.x/actions/create), and
[modal editing](https://filamentphp.com/docs/5.x/actions/edit).

## Authorization and tenancy

Read the installed major version's tenancy documentation and the application's
panel configuration. Automatic scoping depends on model registration, panel
context, and version; do not assume every relationship is scoped or every one
requires the same manual workaround.

1. Verify panel membership, record policy checks, route lookup, relationship
   validation, and custom actions. Exercise a forged related ID from another
   tenant; filtering a dropdown alone is not evidence of secure saving.
2. When a relationship query needs an additional scope, current Filament 5 Select
   uses the `modifyQueryUsing` argument on `relationship()`:

   ```php
   Select::make('category_id')
       ->relationship(
           name: 'category',
           titleAttribute: 'name',
           modifyQueryUsing: fn (Builder $query) => $query
               ->where('tenant_id', $authorizedTenantId),
       );
   ```

   Import the appropriate Select and Eloquent Builder classes. Resolve
   `$authorizedTenantId` from trusted, authorized context, not form data. Confirm
   the model's tenant key and installed version. Do not chain a made-up Select
   `modifyQueryUsing()` method.
3. Laravel's database `unique`/`exists` rules do not inherently apply Eloquent
   scopes. Where supported and appropriate, Filament `scopedUnique()` and
   `scopedExists()` use model scopes. Otherwise constrain validation explicitly.
   Match actual database uniqueness rules; some values are deliberately global.
4. Recheck business preconditions at action execution, especially after opening
   a modal or selecting bulk records. Use native action/policy checks and the
   owning operation. Do not implement correctness solely through visibility.
5. Define bulk failure semantics: all-or-nothing when the invariant requires it,
   or explicitly reported per-record success/failure. Apply per-record access
   and avoid treating a partial result as full success.
6. For queued imports/exports/actions, carry and re-establish the authorized tenant
   context using the application's conventions. Ensure downloadable output and
   notifications remain accessible only to intended users.

Sources: [Filament 5 Select](https://filamentphp.com/docs/5.x/forms/select),
[tenancy](https://filamentphp.com/docs/5.x/users/tenancy), and
[security](https://filamentphp.com/docs/5.x/security/overview).
